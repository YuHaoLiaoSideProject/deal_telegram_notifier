"""Tests for sources/base.py — Deal dataclass & BaseSource ABC."""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timezone

import pytest


# ── Deal dataclass ──────────────────────────────────────────────

class TestDeal:
    """Deal 資料結構基本功能測試."""

    def test_deal_creation_with_all_fields(self):
        """確認 Deal 可用所有欄位建立."""
        from src.sources.base import Deal

        deal = Deal(
            title="遊戲 A",
            description="一款精彩的動作冒險遊戲",
            url="https://store.epicgames.com/game-a",
            image_url="https://cdn.epic.com/cover.jpg",
            source="epic_free",
            source_id="epic_free_game-a-20260728",
            end_date="2026-07-28T23:59:00Z",
        )

        assert deal.title == "遊戲 A"
        assert deal.description == "一款精彩的動作冒險遊戲"
        assert deal.url == "https://store.epicgames.com/game-a"
        assert deal.image_url == "https://cdn.epic.com/cover.jpg"
        assert deal.source == "epic_free"
        assert deal.source_id == "epic_free_game-a-20260728"
        assert deal.end_date == "2026-07-28T23:59:00Z"

    def test_deal_creation_with_minimal_fields(self):
        """確認 Deal 只需要必填欄位即可建立."""
        from src.sources.base import Deal

        deal = Deal(
            title="遊戲 B",
            url="https://store.epicgames.com/game-b",
            source="epic_free",
            source_id="epic_free_game-b-20260728",
        )

        assert deal.title == "遊戲 B"
        assert deal.description is None
        assert deal.image_url is None
        assert deal.end_date is None

    def test_deal_repr(self):
        """確認 Deal 有清楚的 repr 方便除錯."""
        from src.sources.base import Deal

        deal = Deal(title="遊戲 A", url="https://...", source="epic_free", source_id="id-1")
        r = repr(deal)

        assert "Deal" in r
        assert "遊戲 A" in r
        assert "epic_free" in r

    def test_deal_equality_by_source_id(self):
        """確認相同 source_id 視為同一筆 Deal."""
        from src.sources.base import Deal

        d1 = Deal(title="遊戲 A", url="https://a", source="epic_free", source_id="id-1")
        d2 = Deal(title="遊戲 A", url="https://a", source="epic_free", source_id="id-1")

        # dataclass 預設比對所有欄位
        assert d1 == d2


# ── BaseSource ABC ──────────────────────────────────────────────

class TestBaseSource:
    """BaseSource 抽象基底類別測試."""

    def test_cannot_instantiate_base_source_directly(self):
        """確認 BaseSource 不能直接實例化."""
        from src.sources.base import BaseSource

        with pytest.raises(TypeError):
            BaseSource()  # 抽象類別應拋出 TypeError

    def test_concrete_source_must_implement_abstract_methods(self):
        """確認繼承者未實作抽象方法時會拋錯."""
        from src.sources.base import BaseSource

        with pytest.raises(TypeError):

            class Incomplete(BaseSource):
                pass

            Incomplete()

    def test_concrete_source_works(self):
        """確認完整實作後可正常使用."""
        from src.sources.base import BaseSource, Deal

        class ConcreteSource(BaseSource):
            @property
            def source_name(self) -> str:
                return "test_source"

            def fetch_deals(self):
                return [
                    Deal(title="Test", url="https://test", source="test", source_id="t1")
                ]

        source = ConcreteSource()
        assert source.source_name == "test_source"
        deals = source.fetch_deals()
        assert len(deals) == 1
        assert deals[0].title == "Test"
