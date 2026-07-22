# 🎮 福利好康 TG 通知 — Deal Telegram Notifier

自動爬取 **Epic Games 限時免費遊戲**等優惠資訊，每天定時透過 **Telegram Bot** 推播通知。採用可插拔的 Source 架構設計，未來可輕鬆擴充支援更多資料來源（Steam、GOG 等）。

> 💰 **預算：$0** — 使用 GitHub Actions 免費額度，一天一次爬蟲綽綽有餘。

---

## ✨ 功能特色

- 🕷️ **自動爬取**：透過 Epic Games Store 官方 API 取得當期及下期限免遊戲
- 📢 **Telegram 推播**：格式化訊息包含遊戲名稱、說明、截止日期與商店連結
- 🧠 **去重機制**：以 JSON 記錄已通知的優惠，避免重複發送
- 🧩 **可插拔架構**：透過 `BaseSource` 抽象介面，新增來源只需實作一個 class
- ⏰ **定時排程**：GitHub Actions Cron 每天 UTC 02:00（台北 10:00）自動執行
- ✅ **完整測試**：單元測試涵蓋 Engine、Notifier、Tracker、Source 等核心模組

---

## 🏗️ 架構概覽

```
┌─────────────┐     ┌──────────┐     ┌──────────────┐
│   Source    │────▶│  Engine  │────▶│   Notifier   │───▶ Telegram
│ (epic_free) │     │          │     │ (Bot API)    │
└─────────────┘     │ 協調流程 │     └──────────────┘
                    │          │
┌─────────────┐     │ ┌──────┐ │
│  Source 2   │────▶│ │Tracker│ │
│ (未來擴充)   │     │ │(JSON) │ │
└─────────────┘     │ └──────┘ │
                    └──────────┘
```

**流程說明：**

1. **Source** 爬取各平台優惠，回傳 `Deal` 列表
2. **Engine** 合併多來源資料，去重後交由 **Tracker** 過濾出新優惠
3. 新優惠透過 **Notifier** 格式化後發送至 Telegram
4. **Tracker** 將已通知的優惠寫入 `data/sent_deals.json` 持久化記錄

---

## 📁 專案結構

```
deal_telegram_notifier/
├── src/
│   ├── main.py                  # 入口腳本 — 載入設定並啟動 Engine
│   ├── engine.py                # 排程引擎 — 編排 Source → Tracker → Notifier 流程
│   ├── notifier.py              # Telegram Bot API 通知發送（含重試邏輯）
│   ├── tracker.py               # 已通知記錄管理（JSON 讀寫、去重）
│   ├── __init__.py
│   └── sources/
│       ├── base.py              # BaseSource 抽象類別 + Deal dataclass
│       ├── epic_free.py         # Epic Games 限免遊戲來源實作
│       └── __init__.py
├── tests/
│   ├── test_engine.py           # Engine 編排流程測試
│   ├── test_notifier.py         # Notifier 發送邏輯測試（含請求 mock）
│   ├── test_tracker.py          # Tracker JSON 記錄管理測試
│   ├── test_epic_free_source.py # Epic Free 來源解析測試
│   ├── test_sources_base.py     # Deal 資料結構與 BaseSource 測試
│   └── __init__.py
├── features/
│   ├── epic_free_crawler.feature      # BDD: Epic 爬蟲來源
│   ├── epic_free_notification.feature # BDD: Telegram 通知
│   ├── epic_free_tracker.feature      # BDD: 已通知記錄管理
│   └── epic_free_engine.feature       # BDD: 排程引擎
├── docs/
│   └── tech-decision-福利好康TG通知-2026-07-21.md  # 技術方案決策紀錄
├── .github/workflows/
│   └── daily_notify.yml         # GitHub Actions 每日排程工作流程
├── .env.example                 # 環境變數範本
├── requirements.txt             # Python 相依套件
└── .gitignore
```

---

## 🚀 快速開始

### 環境需求

- Python 3.11+
- pip

### 1️⃣ 安裝相依套件

```bash
pip install -r requirements.txt
```

### 2️⃣ 建立 Telegram Bot

1. 在 Telegram 中搜尋 [@BotFather](https://t.me/botfather)
2. 輸入 `/newbot` 並依指示建立 Bot，取得 **Bot Token**
3. 將 Bot 加入你的群組或頻道
4. 取得 **Chat ID**（可透過 `@userinfobot` 或 `https://api.telegram.org/bot<TOKEN>/getUpdates` 查詢）
5. （選用）若使用討論群組的**話題（Thread）**，一併記錄 Thread ID

### 3️⃣ 設定環境變數

複製 `.env.example` 為 `.env` 並填入設定：

```bash
cp .env.example .env
```

```ini
# .env
TELEGRAM_BOT_TOKEN=你的_BOT_TOKEN
TELEGRAM_CHAT_ID=-1003719393573
TELEGRAM_THREAD_ID_DEAL=1018

# DATA_PATH=data/sent_deals.json   # 選填，預設即為此值
```

### 4️⃣ 執行通知

```bash
python -m src.main
```

### 5️⃣ 執行測試

```bash
pytest -v
```

---

## 🤖 GitHub Actions 自動排程

專案已設定 GitHub Actions 每天 **UTC 02:00**（台北時間 10:00）自動執行。

### 設定 Secrets & Variables

前往 **GitHub Repo → Settings → Secrets and variables → Actions** 新增：

| 名稱 | 類型 | 說明 |
|------|------|------|
| `TELEGRAM_BOT_TOKEN` | **Secret** | Telegram Bot Token |
| `TELEGRAM_CHAT_ID` | **Secret** | 接收通知的聊天/群組 ID |
| `TELEGRAM_THREAD_ID_DEAL` | **Variable** | （選用）話題 Thread ID |

> ⚠️ `TELEGRAM_BOT_TOKEN` 與 `TELEGRAM_CHAT_ID` 為敏感資料，請使用 **Secrets** 儲存。  
> `TELEGRAM_THREAD_ID_DEAL` 非敏感，使用 **Variables** 即可。

### 已通知記錄持久化

工作流程執行後會自動將 `data/sent_deals.json` 的變更提交回 Repository，確保下次執行時能正確去重。

---

## 🧩 擴充新資料來源

由於採用 `BaseSource` 抽象介面，新增來源非常簡單：

1. 在 `src/sources/` 下新增檔案（如 `steam.py`）
2. 繼承 `BaseSource` 並實作 `source_name` 與 `fetch_deals()`
3. 在 `src/main.py` 的 `sources` 列表中加入實例

```python
# src/sources/steam.py
from src.sources.base import BaseSource, Deal

class SteamSource(BaseSource):
    @property
    def source_name(self) -> str:
        return "steam"

    def fetch_deals(self) -> list[Deal]:
        # 實作 Steam 優惠爬取邏輯
        ...
```

```python
# src/main.py
engine = Engine(
    sources=[
        EpicFreeSource(),
        SteamSource(),       # ✨ 新增
    ],
    ...
)
```

---

## 📐 核心資料結構

```python
@dataclass
class Deal:
    title: str          # 遊戲/優惠名稱
    url: str            # 商店連結
    source: str         # 來源名稱（如 "epic_free"）
    source_id: str      # 唯一識別碼（用於去重）
    description: str | None   # 說明文字
    image_url: str | None     # 封面圖片
    end_date: str | None      # 截止日期（ISO 格式）
```

---

## 📜 技術決策

詳細的技術方案評估與決策過程請參閱：
[`docs/tech-decision-福利好康TG通知-2026-07-21.md`](docs/tech-decision-福利好康TG通知-2026-07-21.md)

包含方案比較（GitHub Actions vs Cloudflare Workers vs 本地排程）、權衡評估、風險登錄等。

---

## 🧪 BDD 測試腳本

`features/` 目錄以 Gherkin 格式撰寫了完整的行為驅動測試腳本：

| Feature 檔案 | 說明 | 情境數 |
|-------------|------|:------:|
| `epic_free_crawler.feature` | Epic Games 爬蟲來源行為 | 8 |
| `epic_free_notification.feature` | Telegram 通知發送行為 | 7 |
| `epic_free_tracker.feature` | 已通知記錄管理行為 | 7 |
| `epic_free_engine.feature` | 排程引擎編排行爲 | 8 |

---

## ⚙️ 技術棧

| 層級 | 技術 |
|------|------|
| 語言 | Python 3.11+ |
| 爬蟲 | `requests`（Epic Games 公開 API） |
| 通知 | Telegram Bot API（HTTP POST） |
| 排程 | GitHub Actions（Cron） |
| 測試 | pytest + pytest-mock + requests-mock |
| 狀態追蹤 | JSON 檔案（Git 版控） |

---

## 📄 License

MIT
