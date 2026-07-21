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


# ── 必要設定檢查 ──────────────────────────────────────────────

REQUIRED_ENV = {
    "TELEGRAM_BOT_TOKEN": (
        "Secret — Telegram Bot Token（從 @BotFather 取得）"
    ),
    "TELEGRAM_CHAT_ID": (
        "Secret — 接收通知的聊天/群組 ID"
    ),
}

OPTIONAL_ENV = {
    # Variable — 好康通知話題 thread_id（Repo → Settings → Variables → Actions）
    "TELEGRAM_THREAD_ID_DEAL": "好康通知",
}


def main():
    # ── 檢查必要設定 ─────────────────────────────────────
    missing = []
    for key, hint in REQUIRED_ENV.items():
        if not os.environ.get(key):
            missing.append(f"  • {key}  —  {hint}")

    if missing:
        msg = (
            "╔══════════════════════════════════════════════════╗\n"
            "║   ❌ 缺少必要的 Secrets                         ║\n"
            "╚══════════════════════════════════════════════════╝\n"
            "\n"
            + "\n".join(missing) + "\n"
            "\n"
            "請至 Repo → Settings → Secrets and variables → Actions 新增。\n"
            "若在 Organization 層級新增，請確認「Repository access」有勾選此 Repo。\n"
        )
        logger.error(msg)
        sys.exit(1)

    # ── 載入設定 ─────────────────────────────────────────
    bot_token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    data_path = os.environ.get("DATA_PATH", "data/sent_deals.json")

    # 話題設定：未來可依需求新增不同話題
    thread_id_deal = os.environ.get("TELEGRAM_THREAD_ID_DEAL")  # 好康通知

    # ── 啟動引擎 ─────────────────────────────────────────
    engine = Engine(
        sources=[EpicFreeSource()],
        notifier=Notifier(
            bot_token=bot_token,
            chat_id=chat_id,
            thread_id=thread_id_deal,
        ),
        tracker=Tracker(json_path=data_path),
    )

    logger.info("開始執行福利好康通知...")
    engine.run()
    logger.info("執行完畢")


if __name__ == "__main__":
    main()
