"""Tests for notifier.py — Telegram 通知發送."""

import pytest


class TestNotifier:
    """Notifier Telegram 通知功能測試."""

    def test_send_single_deal_success(self, requests_mock):
        """確認成功發送單一遊戲通知."""
        from src.notifier import Notifier
        from src.sources.base import Deal

        requests_mock.post(
            "https://api.telegram.org/bot123456:ABC-DEF1234ghIkl/sendMessage",
            json={"ok": True},
            status_code=200,
        )

        notifier = Notifier(bot_token="123456:ABC-DEF1234ghIkl", chat_id="987654")
        deal = Deal(title="遊戲 A", url="https://store.epicgames.com/a", source="epic_free", source_id="id-1")

        result = notifier.send(deal)
        assert result is True

    def test_send_message_format(self, requests_mock):
        """確認發送的訊息格式正確."""
        from src.notifier import Notifier
        from src.sources.base import Deal

        def check_request(request, context):
            import json
            data = json.loads(request.body)
            assert data["chat_id"] == "987654"
            assert "🎮" in data["text"]
            assert "遊戲 A" in data["text"]
            assert "store.epicgames.com" in data["text"]
            return {"ok": True}

        adapter = requests_mock.post(
            "https://api.telegram.org/bot12345:token/sendMessage",
            json=check_request,
        )

        notifier = Notifier(bot_token="12345:token", chat_id="987654")
        deal = Deal(title="遊戲 A", url="https://store.epicgames.com/a", source="epic_free", source_id="id-1")

        notifier.send(deal)
        assert adapter.called_once

    def test_send_batch_merged_message(self, requests_mock):
        """確認多筆遊戲合併為一則訊息."""
        from src.notifier import Notifier
        from src.sources.base import Deal

        def check_request(request, context):
            import json
            data = json.loads(request.body)
            assert "遊戲 A" in data["text"]
            assert "遊戲 B" in data["text"]
            assert "遊戲 C" in data["text"]
            return {"ok": True}

        adapter = requests_mock.post(
            "https://api.telegram.org/bot12345:token/sendMessage",
            json=check_request,
        )

        notifier = Notifier(bot_token="12345:token", chat_id="987654")
        deals = [
            Deal(title="遊戲 A", url="https://a", source="epic_free", source_id="id-1"),
            Deal(title="遊戲 B", url="https://b", source="epic_free", source_id="id-2"),
            Deal(title="遊戲 C", url="https://c", source="epic_free", source_id="id-3"),
        ]

        notifier.send_batch(deals)
        assert adapter.called_once

    def test_send_with_invalid_token(self, requests_mock):
        """確認無效 Token 時拋出 NotificationError."""
        from src.notifier import Notifier, NotificationError
        from src.sources.base import Deal

        requests_mock.post(
            "https://api.telegram.org/botINVALID_TOKEN/sendMessage",
            json={"ok": False, "description": "Unauthorized"},
            status_code=401,
        )

        notifier = Notifier(bot_token="INVALID_TOKEN", chat_id="987654")
        deal = Deal(title="A", url="https://a", source="epic_free", source_id="id-1")

        with pytest.raises(NotificationError, match="Unauthorized"):
            notifier.send(deal)

    def test_send_truncates_long_message(self, requests_mock):
        """確認超過 4096 字元的訊息會被截斷."""
        from src.notifier import Notifier
        from src.sources.base import Deal

        def check_request(request, context):
            import json
            data = json.loads(request.body)
            assert len(data["text"]) <= 4096
            assert "…（內容過長已截斷）" in data["text"]
            return {"ok": True}

        adapter = requests_mock.post(
            "https://api.telegram.org/bot12345:token/sendMessage",
            json=check_request,
        )

        notifier = Notifier(bot_token="12345:token", chat_id="987654")
        deal = Deal(
            title="A",
            url="https://a",
            source="epic_free",
            source_id="id-1",
            description="A" * 5000,
        )

        notifier.send(deal)
        assert adapter.called_once

    def test_rate_limit_retry(self, requests_mock):
        """確認 429 時自動重試（最多 3 次）."""
        from src.notifier import Notifier, NotificationError
        from src.sources.base import Deal

        # 前 3 次回 429，第 4 次回 200（但我們只重試 3 次，所以應拋錯）
        adapter = requests_mock.post(
            "https://api.telegram.org/bot12345:token/sendMessage",
            [
                {"json": {"ok": False}, "status_code": 429},
                {"json": {"ok": False}, "status_code": 429},
                {"json": {"ok": False}, "status_code": 429},
            ],
        )

        notifier = Notifier(bot_token="12345:token", chat_id="987654", max_retries=3)
        deal = Deal(title="A", url="https://a", source="epic_free", source_id="id-1")

        with pytest.raises(NotificationError):
            notifier.send(deal)

        assert adapter.call_count == 3

    def test_send_special_characters(self, requests_mock):
        """確認特殊字元能正確發送."""
        from src.notifier import Notifier
        from src.sources.base import Deal

        def check_request(request, context):
            import json
            data = json.loads(request.body)
            assert "®" in data["text"]
            assert "™" in data["text"]
            assert "🎮" in data["text"]
            return {"ok": True}

        adapter = requests_mock.post(
            "https://api.telegram.org/bot12345:token/sendMessage",
            json=check_request,
        )

        notifier = Notifier(bot_token="12345:token", chat_id="987654")
        deal = Deal(
            title="Game®™🎮",
            url="https://a",
            source="epic_free",
            source_id="id-1",
        )

        notifier.send(deal)
        assert adapter.called_once
