"""LLM-powered product opportunity analysis for trending keywords."""

import json
import logging
import re
from datetime import date
from pathlib import Path

from openai import OpenAI

logger = logging.getLogger("trend_agent")

ANALYSIS_PROMPT = """Analyze this trending keyword for international e-commerce opportunity.

Keyword: {keyword}
Region: {region}

Return ONLY a JSON object (no markdown fences) with these fields:
- product_category: string
- example_products: list of 2-3 product names
- target_market: list of country codes
- demand_score: integer 1-10
- sourcing_difficulty: integer 1-10
- shipping_difficulty: integer 1-10
- profit_potential: integer 1-10
- reasoning: one sentence explaining the opportunity
"""


def _parse_llm_json(text: str) -> dict | None:
    """Extract JSON from LLM response, tolerating markdown fences."""
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if m:
        text = m.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def analyze_keyword(client: OpenAI, model: str, keyword: str, region: str) -> dict | None:
    """Analyze a single keyword via LLM. Returns structured dict or None on failure."""
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": ANALYSIS_PROMPT.format(keyword=keyword, region=region)}],
            temperature=0.3,
            max_tokens=500,
        )
        raw = resp.choices[0].message.content
        parsed = _parse_llm_json(raw)
        if parsed is None:
            logger.warning("Failed to parse LLM JSON for keyword '%s'", keyword)
            return None
        parsed["keyword"] = keyword
        parsed["source_region"] = region
        return parsed
    except Exception as e:
        logger.warning("LLM analysis failed for '%s': %s", keyword, e)
        return None


def run_analysis(trends_path: str, data_dir: str, llm_config: dict) -> str:
    """Analyze all trending keywords from a trends file. Returns output path."""
    with open(trends_path, encoding="utf-8") as f:
        trends_data = json.load(f)

    client = OpenAI(api_key=llm_config["api_key"], base_url=llm_config["base_url"])
    model = llm_config["model"]

    seen_keywords: set[str] = set()
    opportunities: list[dict] = []

    for region_block in trends_data:
        region = region_block["region"]
        for trend in region_block.get("trends", []):
            kw = trend["keyword"].lower().strip()
            if kw in seen_keywords:
                continue
            seen_keywords.add(kw)

            result = analyze_keyword(client, model, trend["keyword"], region)
            if result:
                opportunities.append(result)
                logger.info("Analyzed: %s (profit=%s)", kw, result.get("profit_potential"))

    today = date.today().isoformat()
    out_dir = Path(data_dir) / "opportunities"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{today}.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(opportunities, f, indent=2, ensure_ascii=False)

    logger.info("Opportunity analysis saved to %s (%d items)", out_path, len(opportunities))
    return str(out_path)
