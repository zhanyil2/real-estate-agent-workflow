"""Generate a human-readable daily report from opportunity analysis."""

import json
import logging
from datetime import date
from pathlib import Path

logger = logging.getLogger("trend_agent")


def generate_report(opportunities_path: str, top_n: int = 10) -> str:
    """Load opportunities, rank by profit_potential, return formatted report text."""
    with open(opportunities_path, encoding="utf-8") as f:
        opportunities = json.load(f)

    ranked = sorted(opportunities, key=lambda x: x.get("profit_potential", 0), reverse=True)
    top = ranked[:top_n]
    today = date.today().isoformat()

    lines = [
        "📊 Daily International E-commerce Opportunities",
        f"Date: {today}",
        f"Analyzed: {len(opportunities)} keywords | Showing top {len(top)}",
        "=" * 45,
        "",
    ]

    for i, opp in enumerate(top, 1):
        markets = ", ".join(opp.get("target_market", []))
        products = opp.get("example_products", [])
        lines.append(f"{i}. {opp.get('keyword', 'N/A')}")
        lines.append(f"   Category: {opp.get('product_category', 'N/A')}")
        lines.append(f"   Demand: {opp.get('demand_score', '?')}/10")
        lines.append(f"   Profit Potential: {opp.get('profit_potential', '?')}/10")
        lines.append(f"   Sourcing Difficulty: {opp.get('sourcing_difficulty', '?')}/10")
        lines.append(f"   Shipping Difficulty: {opp.get('shipping_difficulty', '?')}/10")
        lines.append(f"   Target Market: {markets}")
        if products:
            lines.append("   Suggested Products:")
            for p in products:
                lines.append(f"   - {p}")
        if opp.get("reasoning"):
            lines.append(f"   Note: {opp['reasoning']}")
        lines.append("")

    report_text = "\n".join(lines)

    report_dir = Path(opportunities_path).parent.parent / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / f"{today}.txt"
    report_file.write_text(report_text, encoding="utf-8")

    logger.info("Report generated: %s (%d opportunities)", report_file, len(top))
    return report_text
