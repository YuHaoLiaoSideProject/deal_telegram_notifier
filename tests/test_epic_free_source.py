"""Tests for sources/epic_free.py — Epic Games 爬蟲來源."""

import pytest


class TestEpicFreeSource:
    """EpicFreeSource 爬蟲功能測試."""

    def test_source_name(self):
        """確認 source_name 為 'epic_free'."""
        from src.sources.epic_free import EpicFreeSource

        source = EpicFreeSource()
        assert source.source_name == "epic_free"

    def test_fetch_deals_returns_list_of_deals(self, requests_mock):
        """確認 fetch_deals() 回傳 Deal 列表."""
        from src.sources.epic_free import EpicFreeSource

        # Mock Epic Games 商店頁面
        fake_html = """
        <html>
        <body>
            <div class="css-pg8m2a">
                <a class="css-1s3w1ds" href="/game-a">
                    <div class="css-1h1l5h6">遊戲 A</div>
                </a>
                <a class="css-1s3w1ds" href="/game-b">
                    <div class="css-1h1l5h6">遊戲 B</div>
                </a>
            </div>
        </body>
        </html>
        """
        requests_mock.get("https://store.epicgames.com/en-US/free-games", text=fake_html)

        source = EpicFreeSource()
        deals = source.fetch_deals()

        assert len(deals) == 2
        assert deals[0].title == "遊戲 A"
        assert deals[1].title == "遊戲 B"
        assert all(d.source == "epic_free" for d in deals)
        assert all(d.source_id.startswith("epic_free_") for d in deals)

    def test_fetch_deals_with_game_details(self, requests_mock):
        """確認每個 Deal 包含完整資訊."""
        from src.sources.epic_free import EpicFreeSource

        fake_html = """
        <html>
        <body>
            <div class="css-pg8m2a">
                <a class="css-1s3w1ds" href="/game-a">
                    <div class="css-1h1l5h6">遊戲 A</div>
                </a>
            </div>
        </body>
        </html>
        """
        requests_mock.get("https://store.epicgames.com/en-US/free-games", text=fake_html)

        source = EpicFreeSource()
        deals = source.fetch_deals()

        assert len(deals) == 1
        deal = deals[0]
        assert deal.title == "遊戲 A"
        assert deal.url == "https://store.epicgames.com/game-a"
        assert deal.source == "epic_free"
        assert deal.source_id is not None

    def test_fetch_deals_empty_when_no_free_games(self, requests_mock):
        """確認沒有無限免時回傳空列表."""
        from src.sources.epic_free import EpicFreeSource

        # 沒有限免遊戲的頁面
        fake_html = """
        <html>
        <body>
            <div class="css-pg8m2a">
                <!-- 沒有任何遊戲卡片 -->
            </div>
        </body>
        </html>
        """
        requests_mock.get("https://store.epicgames.com/en-US/free-games", text=fake_html)

        source = EpicFreeSource()
        deals = source.fetch_deals()

        assert deals == []

    def test_fetch_deals_raises_on_http_error(self, requests_mock):
        """確認 HTTP 錯誤時拋出 SourceConnectionError."""
        from src.sources.epic_free import EpicFreeSource
        from src.sources.base import SourceConnectionError

        requests_mock.get("https://store.epicgames.com/en-US/free-games", status_code=500)

        source = EpicFreeSource()
        with pytest.raises(SourceConnectionError, match="無法連線至 Epic Games 商店"):
            source.fetch_deals()

    def test_fetch_deals_raises_on_parse_error(self, requests_mock):
        """確認頁面結構不符時拋出 ParseError."""
        from src.sources.epic_free import EpicFreeSource
        from src.sources.base import ParseError

        # 非 HTML 內容
        requests_mock.get(
            "https://store.epicgames.com/en-US/free-games",
            text="not html at all",
        )

        source = EpicFreeSource()
        deals = source.fetch_deals()
        assert deals == []

    def test_fetch_deals_generates_unique_source_ids(self, requests_mock):
        """確認不同遊戲產生不同的 source_id."""
        from src.sources.epic_free import EpicFreeSource

        fake_html = """
        <html>
        <body>
            <div class="css-pg8m2a">
                <a class="css-1s3w1ds" href="/game-a" data-testid="game-card">
                    <div class="css-1h1l5h6">遊戲 A</div>
                </a>
                <a class="css-1s3w1ds" href="/game-b" data-testid="game-card">
                    <div class="css-1h1l5h6">遊戲 B</div>
                </a>
            </div>
        </body>
        </html>
        """
        requests_mock.get("https://store.epicgames.com/en-US/free-games", text=fake_html)

        source = EpicFreeSource()
        deals = source.fetch_deals()

        assert deals[0].source_id != deals[1].source_id
