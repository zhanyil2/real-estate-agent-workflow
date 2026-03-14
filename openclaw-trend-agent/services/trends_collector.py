"""Google Trends data collection with LLM fallback for restricted networks."""

import json
import logging
import os
import time
from datetime import datetime, date
from pathlib import Path

logger = logging.getLogger("trend_agent")

REGION_MAP = {
    "US": {"geo": "US", "label": "United States"},
    "GB": {"geo": "GB", "label": "Europe (UK proxy)"},
    "JP": {"geo": "JP", "label": "Japan"},
    "SG": {"geo": "SG", "label": "Southeast Asia (SG proxy)"},
}

ECOMMERCE_SEED_KEYWORDS = [
    "best selling products",
    "trending products",
    "new gadgets",
    "home improvement",
    "outdoor gear",
    "pet products",
    "kitchen gadgets",
    "fitness equipment",
    "phone accessories",
    "smart home",
]

LLM_TRENDS_PROMPT = """You are a market research analyst. Generate a list of 15 currently trending product keywords for e-commerce in the {region} ({label}) market as of {date}.

Focus on:
- Products with high consumer demand right now
- Seasonal trends
- Viral/social-media-driven products
- New technology products

Return ONLY a JSON array of objects, each with:
- "keyword": the product/search term
- "trend_score": estimated popularity 1-100
- "trend_direction": "rising" or "stable"
- "related": list of 1-2 related search terms

Example format:
[
  {{"keyword": "portable power station", "trend_score": 92, "trend_direction": "rising", "related": ["solar generator", "camping battery"]}}
]

Return ONLY the JSON array, no markdown fences, no extra text."""


def _collect_region_google(geo: str, max_retries: int = 3) -> list[dict]:
    """Collect trending searches from Google Trends for one region."""
    from pytrends.request import TrendReq

    pytrends = TrendReq(hl="en-US", tz=360, timeout=(10, 30))
    results = []

    for attempt in range(max_retries):
        try:
            pn_map = {"US": "united_states", "JP": "japan", "GB": "united_kingdom", "SG": "singapore"}
            trending = pytrends.trending_searches(pn=pn_map.get(geo, geo.lower()))
            keywords = trending[0].tolist()[:20]

            for kw in keywords:
                results.append({
                    "keyword": kw,
                    "trend_score": 100,
                    "trend_direction": "rising",
                    "related": [],
                })

            for seed in ECOMMERCE_SEED_KEYWORDS[:3]:
                try:
                    pytrends.build_payload([seed], timeframe="now 7-d", geo=geo)
                    related = pytrends.related_queries()
                    if seed in related and related[seed]["rising"] is not None:
                        rising_df = related[seed]["rising"]
                        for _, row in rising_df.head(5).iterrows():
                            results.append({
                                "keyword": row["query"],
                                "trend_score": int(row["value"]) if row["value"] < 1000 else 100,
                                "trend_direction": "rising",
                                "related": [seed],
                            })
                    time.sleep(1)
                except Exception:
                    continue

            logger.info("Collected %d trends for region %s via Google Trends", len(results), geo)
            return results

        except Exception as e:
            logger.warning("Google Trends attempt %d/%d for %s failed: %s", attempt + 1, max_retries, geo, e)
            if attempt < max_retries - 1:
                time.sleep(3 * (attempt + 1))

    return results


def _collect_region_llm(region: str, label: str, llm_config: dict) -> list[dict]:
    """Fallback: use LLM to generate plausible trending keywords when Google is unreachable."""
    from openai import OpenAI

    logger.info("Using LLM fallback for trends in %s", region)
    client = OpenAI(api_key=llm_config["api_key"], base_url=llm_config["base_url"])

    prompt = LLM_TRENDS_PROMPT.format(
        region=region,
        label=label,
        date=date.today().isoformat(),
    )

    try:
        resp = client.chat.completions.create(
            model=llm_config["model"],
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000,
        )
        raw = resp.choices[0].message.content.strip()

        import re
        m = re.search(r"\[.*\]", raw, re.DOTALL)
        if m:
            raw = m.group(0)

        trends = json.loads(raw)
        if isinstance(trends, list):
            logger.info("LLM generated %d trends for region %s", len(trends), region)
            return trends
    except Exception as e:
        logger.error("LLM fallback failed for %s: %s", region, e)

    return []


def _test_google_reachable() -> bool:
    """Quick check whether Google Trends is reachable."""
    import socket
    try:
        socket.create_connection(("trends.google.com", 443), timeout=5)
        return True
    except (OSError, socket.timeout):
        return False


def collect_trends(regions: list[str], data_dir: str, max_retries: int = 3,
                   llm_config: dict | None = None) -> str:
    """Collect trends for all regions and save to JSON. Returns the output path.

    If Google Trends is unreachable and llm_config is provided, falls back to
    LLM-generated trend keywords.
    """
    today = date.today().isoformat()
    out_dir = Path(data_dir) / "trends"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{today}.json"

    google_ok = _test_google_reachable()
    if not google_ok:
        logger.warning("Google Trends unreachable — will use LLM fallback")

    all_data = []

    for region in regions:
        cfg = REGION_MAP.get(region, {"geo": region, "label": region})

        if google_ok:
            trends = _collect_region_google(cfg["geo"], max_retries)
        else:
            trends = []

        if not trends and llm_config:
            trends = _collect_region_llm(region, cfg["label"], llm_config)

        all_data.append({
            "date": today,
            "region": region,
            "region_label": cfg["label"],
            "trends": trends,
            "source": "google_trends" if google_ok and trends else "llm_fallback",
        })

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)

    logger.info("Trends saved to %s (%d regions)", out_path, len(all_data))
    return str(out_path)
