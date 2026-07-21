"""Telegram 通知發送模組."""

import logging
import time
from typing import List

import requests

from src.sources.base import Deal

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"
MAX_MESSAGE_LENGTH = 4096


class NotificationError(Exception):
    """通知發送失敗."""


class Notifier:
    """透過 Telegram Bot API 發送通知."""

    def __init__(self, bot_token: str, chat_id: str, thread_id: str = None, max_retries: int = 3):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.thread_id = thread_id
        self.max_retries = max_retries

    def _api_url(self) -> str:
        return TELEGRAM_API.format(token=self.bot_token)

    def _build_message(self, deal: Deal) -> str:
        """建立單一遊戲通知訊息."""
        lines = [
            f"🎮 {deal.title}",
        ]
        if deal.description:
            lines.append(f"\n{deal.description}")
        if deal.end_date:
            lines.append(f"\n📅 截止：{deal.end_date}")
        lines.append(f"\n🔗 {deal.url}")
        return "\n".join(lines)

    def _build_batch_message(self, deals: List[Deal]) -> str:
        """建立多筆遊戲合併通知訊息."""
        parts = ["🎮 本期限時免費遊戲\n"]
        for i, deal in enumerate(deals, 1):
            parts.append(f"{i}. {deal.title}")
            if deal.end_date:
                parts.append(f"   📅 截止：{deal.end_date}")
            parts.append(f"   🔗 {deal.url}")
            if i < len(deals):
                parts.append("")
        return "\n".join(parts)

    def _truncate(self, text: str) -> str:
        """若訊息超過長度限制則截斷."""
        if len(text) <= MAX_MESSAGE_LENGTH:
            return text
        return text[: MAX_MESSAGE_LENGTH - 20] + "\n\n…（內容過長已截斷）"

    def send(self, deal: Deal) -> bool:
        """發送單一遊戲通知."""
        text = self._truncate(self._build_message(deal))
        return self._post(text)

    def send_batch(self, deals: List[Deal]) -> bool:
        """合併發送多筆遊戲通知."""
        if not deals:
            return False
        text = self._truncate(self._build_batch_message(deals))
        return self._post(text)

    def _post(self, text: str) -> bool:
        """發送 HTTP POST 到 Telegram Bot API，含重試邏輯."""
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                payload = {"chat_id": self.chat_id, "text": text}
                if self.thread_id:
                    payload["message_thread_id"] = int(self.thread_id)
                resp = requests.post(
                    self._api_url(),
                    json=payload,
                    timeout=15,
                )

                if resp.status_code == 200:
                    return True

                # Rate limit - 重試
                if resp.status_code == 429:
                    wait = min(2 ** attempt, 30)
                    logger.warning(
                        "Rate limited, retrying in %ds (attempt %d/%d)",
                        wait,
                        attempt,
                        self.max_retries,
                    )
                    time.sleep(wait)
                    last_error = NotificationError("Rate limited")
                    continue

                # 其他錯誤
                error_msg = resp.json().get("description", str(resp.status_code))
                raise NotificationError(error_msg)

            except requests.RequestException as e:
                last_error = NotificationError(str(e))
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)
                continue

        raise last_error or NotificationError("Max retries exceeded")
