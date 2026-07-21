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


# ── GitHub Actions Secrets 檢查 ────────────────────────────────

REQUIRED_SECRETS = {
    "TELEGRAM_BOT_TOKEN": "Telegram Bot Token（從 @BotFather 取得）",
    "TELEGRAM_CHAT_ID": "接收通知的聊天/群組 ID（數字，含負號）",
    "TELEGRAM_THREAD_ID": "話題 ID（Forum Topic 的 message_thread_id）",
}


def main():
    missing = []
    for key, hint in REQUIRED_SECRETS.items():
        val = os.environ.get(key)
        if not val:
            missing.append(f"  • {key}  —  {hint}")

    if missing:
        msg = (
            "╔══════════════════════════════════════════════════╗\n"
            "║   ❌ 缺少必要的 Secrets                         ║\n"
            "╚══════════════════════════════════════════════════╝\n"
            "\n"
            + "\n".join(missing) + "\n"
            "\n"
            "⚠️  Organization secrets 預設不會自動開放給所有 Repo。\n"
            "請至 Repo 層級設定（推薦）：\n"
            "  Repo → Settings → Secrets and variables → Actions → New secret\n"
            "\n"
            "若已在 Organization 層級新增，請檢查該 secret 的「Repository access」\n"
            "是否有勾選這個 Repo。\n"
        )
        logger.error(msg)
        sys.exit(1)

    bot_token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    thread_id = os.environ.get("TELEGRAM_THREAD_ID")
    data_path = os.environ.get("DATA_PATH", "data/sent_deals.json")

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
