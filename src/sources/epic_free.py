"""Epic Games 限時免費遊戲來源 — 使用 Epic Store 公開 API."""

import hashlib
from typing import List, Optional

import requests

from src.sources.base import (
    BaseSource,
    Deal,
    SourceConnectionError,
)

EPIC_API = (
    "https://store-site-backend-static.ak.epicgames.com/"
    "freeGamesPromotions"
    "?locale=en-US&country=TW&allowCountries=TW"
)
EPIC_BASE = "https://store.epicgames.com"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


class EpicFreeSource(BaseSource):
    """從 Epic Games Store 公開 API 取得限時免費遊戲."""

    @property
    def source_name(self) -> str:
        return "epic_free"

    def fetch_deals(self) -> List[Deal]:
        """呼叫 Epic 官方 API，回傳當期與下期限免 Deal 列表."""
        try:
            resp = requests.get(EPIC_API, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            status = ""
            if hasattr(e, "response") and e.response is not None:
                status = f" (HTTP {e.response.status_code})"
            raise SourceConnectionError(
                f"無法連線至 Epic Games 商店{status}: {e}"
            ) from e
        except ValueError as e:
            raise SourceConnectionError(
                f"Epic API 回傳非 JSON 格式: {e}"
            ) from e

        return self._parse_response(data)

    def _parse_response(self, data: dict) -> List[Deal]:
        """解析 API 回傳的 JSON，回傳 Deal 列表."""
        elements = (
            data.get("data", {})
            .get("Catalog", {})
            .get("searchStore", {})
            .get("elements", [])
        )

        deals: List[Deal] = []

        for el in elements:
            promotions = el.get("promotions")
            if not promotions:
                continue

            # 當期 + 下期免費 promotion
            all_offers = []
            for offer_set in promotions.get("promotionalOffers", []):
                all_offers.extend(offer_set.get("promotionalOffers", []))
            for offer_set in promotions.get("upcomingPromotionalOffers", []):
                all_offers.extend(offer_set.get("promotionalOffers", []))

            for offer in all_offers:
                ds = offer.get("discountSetting", {})
                if ds.get("discountPercentage") != 0:
                    continue  # 只有 100% off 才算限免

                deal = self._element_to_deal(el, offer)
                if deal:
                    deals.append(deal)

        return deals

    def _element_to_deal(
        self, el: dict, offer: dict
    ) -> Optional[Deal]:
        """將 API element 轉為 Deal 物件."""
        title = el.get("title")
        if not title:
            return None

        # 取得 product slug（用於產生商店連結）
        slug = el.get("productSlug")
        if not slug:
            mappings = el.get("catalogNs", {}).get("mappings", [])
            if mappings:
                slug = mappings[0].get("pageSlug", "")

        url = f"{EPIC_BASE}/en-US/p/{slug}" if slug else ""

        end_date = offer.get("endDate", "")

        description = el.get("description") or el.get("shortDescription") or ""

        # 唯一識別碼：用 title + endDate hash
        unique_str = f"{title}-{end_date}"
        source_id = f"epic_free_{hashlib.md5(unique_str.encode()).hexdigest()[:12]}"

        return Deal(
            title=title,
            url=url,
            source="epic_free",
            source_id=source_id,
            description=description.strip(),
            end_date=end_date,
        )
