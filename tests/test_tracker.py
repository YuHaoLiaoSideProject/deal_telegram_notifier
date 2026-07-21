"""Tests for tracker.py — 已通知記錄管理."""

import json
from pathlib import Path

import pytest


class TestTracker:
    """Tracker 已通知記錄管理功能測試."""

    def test_init_creates_file_if_not_exists(self, tmp_path):
        """確認初始化時若檔案不存在會自動建立."""
        from src.tracker import Tracker

        json_path = tmp_path / "sent_deals.json"
        tracker = Tracker(str(json_path))

        assert json_path.exists()
        assert json.loads(json_path.read_text()) == []

    def test_filter_new_all_new_deals(self, tmp_path):
        """確認全部為新遊戲時回傳全部."""
        from src.tracker import Tracker
        from src.sources.base import Deal

        tracker = Tracker(str(tmp_path / "sent_deals.json"))

        deals = [
            Deal(title="A", url="https://a", source="epic_free", source_id="id-1"),
            Deal(title="B", url="https://b", source="epic_free", source_id="id-2"),
        ]

        new = tracker.filter_new(deals)
        assert len(new) == 2

    def test_filter_new_excludes_sent_deals(self, tmp_path):
        """確認已通知過的遊戲會被排除."""
        from src.tracker import Tracker
        from src.sources.base import Deal

        tracker = Tracker(str(tmp_path / "sent_deals.json"))

        deal_a = Deal(title="A", url="https://a", source="epic_free", source_id="id-1")
        deal_b = Deal(title="B", url="https://b", source="epic_free", source_id="id-2")
        deal_c = Deal(title="C", url="https://c", source="epic_free", source_id="id-3")

        # 先標記 A 和 B 為已通知
        tracker.mark_sent(deal_a)
        tracker.mark_sent(deal_b)

        # 過濾
        new = tracker.filter_new([deal_a, deal_b, deal_c])
        assert len(new) == 1
        assert new[0].source_id == "id-3"

    def test_mark_sent_adds_to_file(self, tmp_path):
        """確認 mark_sent 正確寫入 JSON 檔案."""
        from src.tracker import Tracker
        from src.sources.base import Deal

        json_path = tmp_path / "sent_deals.json"
        tracker = Tracker(str(json_path))

        deal = Deal(title="A", url="https://a", source="epic_free", source_id="id-1")
        tracker.mark_sent(deal)

        records = json.loads(json_path.read_text())
        assert len(records) == 1
        assert records[0]["source_id"] == "id-1"
        assert "notified_at" in records[0]

    def test_mark_sent_duplicate_is_idempotent(self, tmp_path):
        """確認重複標記同一遊戲不會產生重複記錄."""
        from src.tracker import Tracker
        from src.sources.base import Deal

        tracker = Tracker(str(tmp_path / "sent_deals.json"))

        deal = Deal(title="A", url="https://a", source="epic_free", source_id="id-1")
        tracker.mark_sent(deal)
        tracker.mark_sent(deal)

        records = json.loads((tmp_path / "sent_deals.json").read_text())
        assert len(records) == 1

    def test_corrupted_json_file(self, tmp_path):
        """確認 JSON 損毀時不拋錯，視為空集合."""
        from src.tracker import Tracker

        json_path = tmp_path / "sent_deals.json"
        json_path.write_text("not valid json{{{")

        tracker = Tracker(str(json_path))
        new = tracker.filter_new([])

        assert new == []

    def test_tracker_persistence_across_instances(self, tmp_path):
        """確認不同 Tracker 實體共享同一份記錄."""
        from src.tracker import Tracker
        from src.sources.base import Deal

        json_path = tmp_path / "sent_deals.json"

        tracker1 = Tracker(str(json_path))
        deal = Deal(title="A", url="https://a", source="epic_free", source_id="id-1")
        tracker1.mark_sent(deal)

        tracker2 = Tracker(str(json_path))
        assert tracker2.is_sent("id-1") is True
        assert tracker2.is_sent("id-999") is False

    def test_large_number_of_records(self, tmp_path):
        """確認大量記錄下 filter_new 效能正常."""
        from src.tracker import Tracker
        from src.sources.base import Deal

        tracker = Tracker(str(tmp_path / "sent_deals.json"))

        # 建立 10000 筆已通知記錄
        for i in range(10000):
            tracker.mark_sent(
                Deal(
                    title=f"Game {i}",
                    url=f"https://game{i}",
                    source="test",
                    source_id=f"test-{i}",
                )
            )

        # 過濾 1 筆新遊戲 + 1 筆已存在
        new = tracker.filter_new(
            [
                Deal(title="New", url="https://new", source="test", source_id="new-1"),
                Deal(title="Old", url="https://old", source="test", source_id="test-5000"),
            ]
        )

        assert len(new) == 1
        assert new[0].source_id == "new-1"
