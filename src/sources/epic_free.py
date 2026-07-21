"""Epic Games 限時免費遊戲來源."""

import hashlib
import re
from typing import List

import requests
from bs4 import BeautifulSoup

from src.sources.base import (
    AntiScrapingDetected,
    BaseSource,
    Deal,
    ParseError,
    SourceConnectionError,
)

EPIC_FREE_URL = "https://store.epicgames.com/en-US/free-games"
EPIC_BASE = "https://store.epicgames.com"

# Epic Games 限免遊戲卡片的 CSS selector（根據實際頁面結構調整）
GAME_CONTAINER_SELECTOR = "div.css-pg8m2a"
GAME_LINK_SELECTOR = "a.css-1s3w1ds"
GAME_TITLE_SELECTOR = "div.css-1h1l5h6"


class EpicFreeSource(BaseSource):
    """從 Epic Games 商店爬取限時免費遊戲."""

    @property
    def source_name(self) -> str:
        return "epic_free"

    def fetch_deals(self) -> List[Deal]:
        """爬取 Epic Games 限免頁面，回傳 Deal 列表."""
        try:
            resp = requests.get(EPIC_FREE_URL, timeout=30)
            resp.raise_for_status()
        except requests.RequestException as e:
            raise SourceConnectionError(
                f"無法連線至 Epic Games 商店: {e}"
            ) from e

        html = resp.text

        # 檢查是否被反爬蟲阻擋
        if self._detect_anti_scraping(html):
            raise AntiScrapingDetected("偵測到反爬蟲機制")

        try:
            return self._parse_deals(html)
        except Exception as e:
            raise ParseError(f"解析頁面結構失敗: {e}") from e

    def _detect_anti_scraping(self, html: str) -> bool:
        """檢查頁面是否顯示 CAPTCHA 或反爬蟲頁面."""
        signals = [
            "cf-browser-verification",
            "captcha",
            "Please complete the security check",
            "Checking your browser",
        ]
        return any(sig.lower() in html.lower() for sig in signals)

    def _parse_deals(self, html: str) -> List[Deal]:
        """解析 HTML，回傳 Deal 列表."""
        soup = BeautifulSoup(html, "html.parser")
        container = soup.select_one(GAME_CONTAINER_SELECTOR)

        if not container:
            # 可能頁面結構改變，回傳空列表
            return []

        game_links = container.select(GAME_LINK_SELECTOR)
        deals: List[Deal] = []

        for link in game_links:
            title_el = link.select_one(GAME_TITLE_SELECTOR)
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            if not title:
                continue

            href = link.get("href", "")
            full_url = f"{EPIC_BASE}{href}" if href.startswith("/") else href

            # 用 title + url hash 產生唯一的 source_id
            unique_str = f"{title}-{href}"
            source_id = f"epic_free_{hashlib.md5(unique_str.encode()).hexdigest()[:12]}"

            deal = Deal(
                title=title,
                url=full_url,
                source="epic_free",
                source_id=source_id,
            )
            deals.append(deal)

        return deals
