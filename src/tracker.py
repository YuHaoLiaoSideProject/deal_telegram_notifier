"""已通知記錄管理 — 以 JSON 檔案儲存."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Set

from src.sources.base import Deal

logger = logging.getLogger(__name__)


class StorageError(Exception):
    """儲存相關錯誤."""


class Tracker:
    """管理已通知過的優惠記錄，避免重複發送."""

    def __init__(self, json_path: str):
        self.json_path = Path(json_path)
        self._ensure_file()

    def _ensure_file(self):
        """確保 JSON 檔案存在，不存在則建立空陣列."""
        if not self.json_path.exists():
            self.json_path.parent.mkdir(parents=True, exist_ok=True)
            self.json_path.write_text("[]", encoding="utf-8")

    def _load_records(self) -> list:
        """讀取 JSON 檔案中的記錄."""
        try:
            data = self.json_path.read_text(encoding="utf-8")
            return json.loads(data)
        except (json.JSONDecodeError, FileNotFoundError):
            logger.warning("sent_deals.json 損毀，已重置")
            return []

    def _save_records(self, records: list):
        """寫入 JSON 檔案."""
        try:
            self.json_path.write_text(
                json.dumps(records, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as e:
            raise StorageError(f"寫入檔案失敗: {e}") from e

    def _sent_ids(self) -> Set[str]:
        """回傳所有已通知過的 source_id 集合."""
        return {r["source_id"] for r in self._load_records()}

    def is_sent(self, source_id: str) -> bool:
        """檢查特定 source_id 是否已通知過."""
        return source_id in self._sent_ids()

    def filter_new(self, deals: List[Deal]) -> List[Deal]:
        """過濾出尚未通知過的新 Deal."""
        sent = self._sent_ids()
        return [d for d in deals if d.source_id not in sent]

    def mark_sent(self, deal: Deal):
        """將一筆 Deal 標記為已通知."""
        records = self._load_records()

        # 避免重複記錄
        if any(r["source_id"] == deal.source_id for r in records):
            return

        records.append(
            {
                "source_id": deal.source_id,
                "notified_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        self._save_records(records)
