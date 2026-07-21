"""Tests for engine.py — 排程引擎編排測試."""

import pytest


class TestEngine:
    """Engine 編排功能測試."""

    def test_run_full_flow_with_new_deals(self, tmp_path, mocker):
        """確認完整流程：Source → Tracker → Notifier."""
        from src.engine import Engine
        from src.sources.base import Deal

        # Mock Source
        mock_source = mocker.Mock()
        mock_source.source_name = "epic_free"
        mock_source.fetch_deals.return_value = [
            Deal(title="A", url="https://a", source="epic_free", source_id="id-1"),
            Deal(title="B", url="https://b", source="epic_free", source_id="id-2"),
        ]

        # Mock Notifier
        mock_notifier = mocker.Mock()

        # 使用真實 Tracker
        from src.tracker import Tracker
        tracker = Tracker(str(tmp_path / "sent_deals.json"))

        engine = Engine(sources=[mock_source], notifier=mock_notifier, tracker=tracker)
        engine.run()

        # 驗證 notifier 被呼叫（2 筆新遊戲）
        assert mock_notifier.send_batch.called
        called_deals = mock_notifier.send_batch.call_args[0][0]
        assert len(called_deals) == 2

    def test_run_skips_notifier_when_no_new_deals(self, tmp_path, mocker):
        """確認無新遊戲時不發通知."""
        from src.engine import Engine
        from src.sources.base import Deal

        mock_source = mocker.Mock()
        mock_source.source_name = "epic_free"
        mock_source.fetch_deals.return_value = []

        mock_notifier = mocker.Mock()

        from src.tracker import Tracker
        tracker = Tracker(str(tmp_path / "sent_deals.json"))

        engine = Engine(sources=[mock_source], notifier=mock_notifier, tracker=tracker)
        engine.run()

        mock_notifier.send.assert_not_called()
        mock_notifier.send_batch.assert_not_called()

    def test_run_one_source_fails_others_continue(self, tmp_path, mocker):
        """確認單一 Source 失敗不影響其他 Source."""
        from src.engine import Engine
        from src.sources.base import Deal, SourceConnectionError

        mock_source_ok = mocker.Mock()
        mock_source_ok.source_name = "source_ok"
        mock_source_ok.fetch_deals.return_value = [
            Deal(title="Ok", url="https://ok", source="source_ok", source_id="ok-1"),
        ]

        mock_source_fail = mocker.Mock()
        mock_source_fail.source_name = "source_fail"
        mock_source_fail.fetch_deals.side_effect = SourceConnectionError("連線失敗")

        mock_notifier = mocker.Mock()

        from src.tracker import Tracker
        tracker = Tracker(str(tmp_path / "sent_deals.json"))

        engine = Engine(
            sources=[mock_source_ok, mock_source_fail],
            notifier=mock_notifier,
            tracker=tracker,
        )
        engine.run()

        # 仍應發送 OK source 的遊戲
        assert mock_notifier.send_batch.called
        called_deals = mock_notifier.send_batch.call_args[0][0]
        assert len(called_deals) == 1
        assert called_deals[0].source == "source_ok"

    def test_run_all_sources_fail(self, tmp_path, mocker):
        """確認所有 Source 都失敗時不發通知."""
        from src.engine import Engine
        from src.sources.base import SourceConnectionError

        mock_sources = []
        for i in range(2):
            s = mocker.Mock()
            s.source_name = f"source_{i}"
            s.fetch_deals.side_effect = SourceConnectionError("fail")
            mock_sources.append(s)

        mock_notifier = mocker.Mock()

        from src.tracker import Tracker
        tracker = Tracker(str(tmp_path / "sent_deals.json"))

        engine = Engine(sources=mock_sources, notifier=mock_notifier, tracker=tracker)
        engine.run()

        mock_notifier.send.assert_not_called()
        mock_notifier.send_batch.assert_not_called()

    def test_deduplication_across_sources(self, tmp_path, mocker):
        """確認不同 Source 回傳相同 source_id 的 Deal 不會重複通知."""
        from src.engine import Engine
        from src.sources.base import Deal

        mock_source_a = mocker.Mock()
        mock_source_a.source_name = "src_a"
        mock_source_a.fetch_deals.return_value = [
            Deal(title="Game", url="https://game", source="src_a", source_id="game-1"),
        ]

        mock_source_b = mocker.Mock()
        mock_source_b.source_name = "src_b"
        mock_source_b.fetch_deals.return_value = [
            Deal(title="Game", url="https://game", source="src_b", source_id="game-1"),
        ]

        mock_notifier = mocker.Mock()

        from src.tracker import Tracker
        tracker = Tracker(str(tmp_path / "sent_deals.json"))

        engine = Engine(
            sources=[mock_source_a, mock_source_b],
            notifier=mock_notifier,
            tracker=tracker,
        )
        engine.run()

        # 只有 1 筆（去重後）
        called_deals = mock_notifier.send_batch.call_args[0][0]
        assert len(called_deals) == 1
