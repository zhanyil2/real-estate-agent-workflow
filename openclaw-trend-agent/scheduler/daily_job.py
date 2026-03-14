"""Pipeline orchestrator — runs scheduled or on-demand."""

import json
import logging
import sys
import time
from pathlib import Path

import schedule

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from services.trends_collector import collect_trends
from analysis.product_opportunity import run_analysis
from report.daily_report import generate_report
from notification.send_report import send_daily_report


def _load_config() -> dict:
    cfg_path = _PROJECT_ROOT / "config.json"
    with open(cfg_path, encoding="utf-8") as f:
        return json.load(f)


def _setup_logging(config: dict):
    log_path = _PROJECT_ROOT / config.get("log_file", "logs/trend_agent.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(str(log_path), encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def run_pipeline(config: dict | None = None) -> str:
    """Execute the full pipeline: collect → analyze → report → notify.

    Returns the report text (useful for on-demand invocation).
    """
    if config is None:
        config = _load_config()

    logger = logging.getLogger("trend_agent")
    data_dir = str(_PROJECT_ROOT / config.get("data_dir", "data"))
    retries = config.get("max_retries", 3)

    logger.info("=== Pipeline started ===")

    # Step 1: Collect trends
    logger.info("[1/4] Collecting trends data...")
    try:
        trends_path = collect_trends(
            config["regions"], data_dir, retries,
            llm_config=config.get("llm"),
        )
    except Exception as e:
        logger.error("Trend collection failed: %s", e)
        return f"Pipeline failed at trend collection: {e}"

    # Step 2: Analyze opportunities
    logger.info("[2/4] Running LLM opportunity analysis...")
    try:
        opps_path = run_analysis(trends_path, data_dir, config["llm"])
    except Exception as e:
        logger.error("Opportunity analysis failed: %s", e)
        return f"Pipeline failed at analysis: {e}"

    # Step 3: Generate report
    logger.info("[3/4] Generating daily report...")
    try:
        top_n = config.get("top_n_opportunities", 10)
        report_text = generate_report(opps_path, top_n)
    except Exception as e:
        logger.error("Report generation failed: %s", e)
        return f"Pipeline failed at report generation: {e}"

    # Step 4: Send via QQ
    logger.info("[4/4] Sending QQ notification...")
    try:
        send_daily_report(report_text, config.get("qq", {}))
    except Exception as e:
        logger.warning("QQ notification failed (report still generated): %s", e)

    logger.info("=== Pipeline complete ===")
    return report_text


def run_scheduler():
    """Run the pipeline on a daily schedule."""
    config = _load_config()
    _setup_logging(config)
    logger = logging.getLogger("trend_agent")

    hour = config.get("schedule_hour", 8)
    minute = config.get("schedule_minute", 0)
    time_str = f"{hour:02d}:{minute:02d}"

    schedule.every().day.at(time_str).do(run_pipeline, config=config)
    logger.info("Scheduler started — pipeline runs daily at %s", time_str)

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--now":
        config = _load_config()
        _setup_logging(config)
        print(run_pipeline(config))
    else:
        run_scheduler()
