"""資料來源抽象基底類別與資料結構."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional


# ── 自訂例外 ────────────────────────────────────────────────


class SourceError(Exception):
    """資料來源相關錯誤的基底類別."""


class SourceConnectionError(SourceError):
    """無法連線至資料來源."""


class ParseError(SourceError):
    """解析資料來源內容失敗."""


class AntiScrapingDetected(SourceError):
    """偵測到反爬蟲機制."""


# ── 資料結構 ────────────────────────────────────────────────


@dataclass
class Deal:
    """一筆優惠/限免資訊的資料結構."""

    title: str
    url: str
    source: str
    source_id: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    end_date: Optional[str] = None


# ── 抽象基底類別 ────────────────────────────────────────────


class BaseSource(ABC):
    """所有資料來源的統一介面.

    子類別必須實作:
        - source_name (property): 唯一識別名稱
        - fetch_deals(): 回傳 Deal 列表
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        """來源唯一識別名稱，例如 'epic_free'."""
        ...

    @abstractmethod
    def fetch_deals(self) -> List[Deal]:
        """取得目前可獲得的優惠列表."""
        ...
