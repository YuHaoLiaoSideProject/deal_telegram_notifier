"""排程引擎 — 協調 Source、Tracker、Notifier 完成每日通知流程."""

import logging
from typing import List

from src.notifier import Notifier
from src.sources.base import BaseSource, Deal
from src.tracker import Tracker

logger = logging.getLogger(__name__)


class Engine:
    """排程引擎，負責編排完整的通知流程."""

    def __init__(
        self,
        sources: List[BaseSource],
        notifier: Notifier,
        tracker: Tracker,
    ):
        self.sources = sources
        self.notifier = notifier
        self.tracker = tracker

    def run(self):
        """執行完整的通知流程.

        1. 遍歷所有 Source，爬取 Deal
        2. 合併所有 Deal
        3. 透過 Tracker 過濾出新的 Deal
        4. 透過 Notifier 發送通知
        5. 標記已通知
        """
        all_deals: List[Deal] = []
        success_count = 0
        fail_count = 0

        for source in self.sources:
            try:
                deals = source.fetch_deals()
                all_deals.extend(deals)
                success_count += 1
                logger.info(
                    "Source %s 成功，取得 %d 筆 Deal",
                    source.source_name,
                    len(deals),
                )
            except Exception as e:
                fail_count += 1
                logger.error(
                    "Source %s 失敗: %s",
                    source.source_name,
                    e,
                )

        if not all_deals:
            if fail_count and not success_count:
                logger.error("所有資料來源皆無法取得，通知中斷")
            elif fail_count:
                logger.warning("部分來源失敗，成功來源無限免遊戲可通知")
            else:
                logger.info("今日無新限免遊戲")
            return

        # 去重：相同 source_id 只保留第一筆
        seen: set[str] = set()
        unique_deals: List[Deal] = []
        for d in all_deals:
            if d.source_id not in seen:
                seen.add(d.source_id)
                unique_deals.append(d)

        # 過濾出新 Deal
        new_deals = self.tracker.filter_new(unique_deals)

        if not new_deals:
            logger.info("無新的限免遊戲需要通知")
            return

        # 發送通知
        try:
            self.notifier.send_batch(new_deals)
        except Exception as e:
            logger.error("發送通知失敗: %s", e)
            # 即使通知失敗，仍嘗試標記（由 send_batch 實作決定）

        # 標記為已通知
        for deal in new_deals:
            try:
                self.tracker.mark_sent(deal)
            except Exception as e:
                logger.error("標記已通知失敗: %s", e)

        # 記錄摘要
        summary_parts = []
        if success_count:
            summary_parts.append(f"{success_count} 個來源成功")
        if fail_count:
            summary_parts.append(f"{fail_count} 個來源失敗")
        logger.info("執行摘要: %s", ", ".join(summary_parts))
