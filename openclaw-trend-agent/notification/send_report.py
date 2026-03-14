"""Send daily report to QQ user via OpenClaw gateway."""

import json
import logging
from datetime import date
from pathlib import Path

import requests

logger = logging.getLogger("trend_agent")


def send_daily_report(report_text: str, qq_config: dict) -> bool:
    """Send report to QQ via OpenClaw gateway RPC.

    Falls back to saving locally if delivery fails.
    """
    gateway_url = qq_config.get("gateway_url", "http://127.0.0.1:18789")
    token = qq_config.get("gateway_token", "")
    target_user = qq_config.get("target_user", "")

    if not target_user:
        logger.error("No target_user configured for QQ notification")
        _save_fallback(report_text)
        return False

    header_line = report_text.split("\n")[0] if report_text else "Daily report ready"

    try:
        ws_url = gateway_url.replace("http://", "ws://").replace("https://", "wss://")
        payload = {
            "method": "sendMessage",
            "params": {
                "channel": "qqbot",
                "target": target_user,
                "text": report_text[:4000],
            },
        }

        resp = requests.post(
            f"{gateway_url}/__openclaw__/api/v1/message",
            json=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=30,
        )

        if resp.status_code == 200:
            logger.info("Report sent to QQ user %s", target_user)
            return True

        logger.warning("Gateway returned %d: %s", resp.status_code, resp.text[:200])
    except Exception as e:
        logger.warning("QQ delivery failed: %s", e)

    _save_fallback(report_text)
    return False


def _save_fallback(report_text: str):
    """Save report locally when QQ delivery fails."""
    today = date.today().isoformat()
    fallback_dir = Path("data/unsent_reports")
    fallback_dir.mkdir(parents=True, exist_ok=True)
    path = fallback_dir / f"{today}.txt"
    path.write_text(report_text, encoding="utf-8")
    logger.info("Report saved to fallback: %s", path)
