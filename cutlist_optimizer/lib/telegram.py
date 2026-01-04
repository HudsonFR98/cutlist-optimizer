import logging
import requests
from datetime import datetime

from cutlist_optimizer.lib import config


logger = logging.getLogger(__name__)


def _build_markdown_message(title: str, lines: list[str]) -> str:
    parts: list[str] = []
    parts.append(f"*[{config.APP_NAME}] {title}*")
    parts.append(f"`{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}`")
    parts.extend(lines)
    return "\n".join(parts)


def send_telegram_message(text: str) -> bool:
    """Send a plain text message to the configured Telegram chat."""
    try:
        url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": config.TELEGRAM_CHAT_ID,
            "text": text
        }
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code != 200:
            logger.error(f"Telegram sendMessage failed: {resp.status_code} {resp.text}")
            return False
        return True
    except Exception as e:
        logger.error(f"Telegram sendMessage exception: {e}")
        return False


def send_error_notification_telegram(title: str, details: dict | None = None, footer: str | None = None) -> bool:
    """Send a structured error notification via Telegram."""
    lines: list[str] = []
    if details:
        for key, value in details.items():
            lines.append(f"- *{key}*: {value}")
    if footer:
        lines.append(footer)
    message = _build_markdown_message(title, lines)
    return send_telegram_message(message)


