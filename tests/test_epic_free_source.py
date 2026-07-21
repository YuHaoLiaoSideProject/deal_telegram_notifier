"""Tests for sources/epic_free.py — Epic Games 限免來源."""

import json

import pytest


# ── 共用 mock API response ───────────────────────────────────

FREE_GAMES_RESPONSE = {
    "data": {
        "Catalog": {
            "searchStore": {
                "elements": [
                    {
                        "title": "遊戲 A",
                        "productSlug": "game-a",
                        "description": "這是一款精彩的動作冒險遊戲",
                        "promotions": {
                            "promotionalOffers": [
                                {
                                    "promotionalOffers": [
                                        {
                                            "discountSetting": {
                                                "discountPercentage": 0,
                                            },
                                            "endDate": "2026-07-28T15:00:00.000Z",
                                        }
                                    ]
                                }
                            ],
                            "upcomingPromotionalOffers": [],
                        },
                    },
                    {
                        "title": "遊戲 B",
                        "productSlug": "game-b",
                        "promotions": {
                            "promotionalOffers": [
                                {
                                    "promotionalOffers": [
                                        {
                                            "discountSetting": {
                                                "discountPercentage": 0,
                                            },
                                            "endDate": "2026-08-04T15:00:00.000Z",
                                        }
                                    ]
                                }
                            ],
                            "upcomingPromotionalOffers": [],
                        },
                    },
                ]
            }
        }
    }
}

NO_FREE_GAMES_RESPONSE = {
    "data": {
        "Catalog": {
            "searchStore": {
                "elements": [
                    {
                        "title": "折扣遊戲",
                        "productSlug": "discount-game",
                        "promotions": {
                            "promotionalOffers": [
                                {
                                    "promotionalOffers": [
                                        {
                                            "discountSetting": {
                                                "discountPercentage": 50,
                                            },
                                            "endDate": "2026-07-28T15:00:00.000Z",
                                        }
                                    ]
                                }
                            ],
                            "upcomingPromotionalOffers": [],
                        },
                    },
                ]
            }
        }
    }
}

FREE_GAMES_UPCOMING_RESPONSE = {
    "data": {
        "Catalog": {
            "searchStore": {
                "elements": [
                    {
                        "title": "即將免費遊戲",
                        "productSlug": "upcoming-free",
                        "promotions": {
                            "promotionalOffers": [],
                            "upcomingPromotionalOffers": [
                                {
                                    "promotionalOffers": [
                                        {
                                            "discountSetting": {
                                                "discountPercentage": 0,
                                            },
                                            "endDate": "2026-08-11T15:00:00.000Z",
                                        }
                                    ]
                                }
                            ],
                        },
                    },
                ]
            }
        }
    }
}

HTTP_ERROR_RESPONSE_TEXT = "Internal Server Error"


class TestEpicFreeSource:
    """EpicFreeSource API 來源測試."""

    API_URL = (
        "https://store-site-backend-static.ak.epicgames.com/"
        "freeGamesPromotions"
        "?locale=zh-TW&country=TW&allowCountries=TW"
    )

    def test_source_name(self):
        """確認 source_name 為 'epic_free'."""
        from src.sources.epic_free import EpicFreeSource

        source = EpicFreeSource()
        assert source.source_name == "epic_free"

    def test_fetch_deals_returns_list_of_deals(self, requests_mock):
        """確認 fetch_deals() 回傳 Deal 列表."""
        from src.sources.epic_free import EpicFreeSource

        requests_mock.get(self.API_URL, json=FREE_GAMES_RESPONSE)

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

        requests_mock.get(self.API_URL, json=FREE_GAMES_RESPONSE)

        source = EpicFreeSource()
        deals = source.fetch_deals()

        assert len(deals) == 2
        deal = deals[0]
        assert deal.title == "遊戲 A"
        assert deal.url == "https://store.epicgames.com/en-US/p/game-a"
        assert deal.source == "epic_free"
        assert deal.description == "這是一款精彩的動作冒險遊戲"
        assert deal.end_date == "2026-07-28T15:00:00.000Z"
        assert deal.source_id is not None

    def test_fetch_deals_empty_when_no_free_games(self, requests_mock):
        """確認沒有無限免時回傳空列表."""
        from src.sources.epic_free import EpicFreeSource

        requests_mock.get(self.API_URL, json=NO_FREE_GAMES_RESPONSE)

        source = EpicFreeSource()
        deals = source.fetch_deals()

        assert deals == []

    def test_fetch_deals_raises_on_http_error(self, requests_mock):
        """確認 HTTP 錯誤時拋出 SourceConnectionError."""
        from src.sources.epic_free import EpicFreeSource
        from src.sources.base import SourceConnectionError

        requests_mock.get(self.API_URL, status_code=500, text=HTTP_ERROR_RESPONSE_TEXT)

        source = EpicFreeSource()
        with pytest.raises(SourceConnectionError, match="無法連線至 Epic Games 商店"):
            source.fetch_deals()

    def test_fetch_deals_generates_unique_source_ids(self, requests_mock):
        """確認不同遊戲產生不同的 source_id."""
        from src.sources.epic_free import EpicFreeSource

        requests_mock.get(self.API_URL, json=FREE_GAMES_RESPONSE)

        source = EpicFreeSource()
        deals = source.fetch_deals()

        assert deals[0].source_id != deals[1].source_id

    def test_fetch_deals_includes_upcoming(self, requests_mock):
        """確認下期的限免遊戲也會被抓到."""
        from src.sources.epic_free import EpicFreeSource

        requests_mock.get(self.API_URL, json=FREE_GAMES_UPCOMING_RESPONSE)

        source = EpicFreeSource()
        deals = source.fetch_deals()

        assert len(deals) == 1
        assert deals[0].title == "即將免費遊戲"
        assert deals[0].source_id.startswith("epic_free_")
