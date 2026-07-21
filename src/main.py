"""福利好康 TG 通知 — 入口腳本."""

import logging
import os
import sys

from src.engine import Engine
from src.notifier import Notifier
from src.sources.epic_free import EpicFreeSource
from src.tracker import Tracker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("main")


def main():
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    thread_id = os.environ.get("TELEGRAM_THREAD_ID")
    data_path = os.environ.get("DATA_PATH", "data/sent_deals.json")

    if not bot_token or not chat_id:
        logger.error("請設定 TELEGRAM_BOT_TOKEN 與 TELEGRAM_CHAT_ID 環境變數")
        sys.exit(1)

    engine = Engine(
        sources=[EpicFreeSource()],
        notifier=Notifier(bot_token=bot_token, chat_id=chat_id, thread_id=thread_id),
        tracker=Tracker(json_path=data_path),
    )

    logger.info("開始執行福利好康通知...")
    engine.run()
    logger.info("執行完畢")


if __name__ == "__main__":
    main()
