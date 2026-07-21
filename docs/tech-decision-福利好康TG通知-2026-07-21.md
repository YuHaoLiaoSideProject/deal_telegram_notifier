# 開發方案決策文件：福利好康 TG 通知 — Epic 限免

## 📌 決策摘要

| 項目 | 內容 |
|------|------|
| **最終方案** | GitHub Actions + Python 爬蟲（Source 介面可插拔架構） |
| **決策日期** | 2026-07-21 |
| **第一個 Epic** | `epic_free` — Epic Games 限時免費遊戲通知 |
| **使用者角色** | 僅接收通知，無需互動 |
| **共識程度** | ✅ 團隊一致通過 |

---

## 1. 需求回顧

- **專案名稱**：福利好康 TG 通知
- **核心功能**：爬取 Epic Games 限時免費遊戲資訊，每天一次透過 Telegram 發送通知給使用者
- **未來擴充**：可能加入其他爬蟲來源（Steam、GOG 等）或第三方 API
- **預算限制**：$0
- **時程**：無壓力
- **資料來源**：爬蟲為主，預留 API 擴充介面

---

## 2. 候選方案

### 🟢 方案 A：GitHub Actions + Python 爬蟲 ✅ 選擇

| 項目 | 內容 |
|------|------|
| **運作方式** | Python 腳本爬取 Epic Games，GitHub Actions Cron 每天定時執行 |
| **爬蟲** | `requests` + `BeautifulSoup4`（必要時加 `Playwright`） |
| **通知** | Telegram Bot API（HTTP POST） |
| **狀態追蹤** | JSON 檔記錄已通知遊戲 |
| **費用** | ✅ **完全免費** |

### 🟡 方案 B：Cloudflare Workers + JavaScript

- 爬蟲 CPU 時間限制（30ms 免費方案），爬 Epic Games SPA 頁面不足

### 🔵 方案 C：本地排程

- 需要 24h 開機，不符無伺服器需求

---

## 3. 權衡評估

| 維度 | 🟢 GitHub Actions | 🟡 Cloudflare Workers | 🔵 本地排程 |
|------|:---:|:---:|:---:|
| 🎯 需求符合度 | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| ⚡ 開發速度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 🔧 維護成本 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| 📈 擴充性 | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 👥 團隊熟悉度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 💰 基礎設施成本 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 🔒 穩定性 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |

### 關鍵取捨分析

**爬蟲 vs API 應變策略**：設計 Source 抽象介面，未來可無痛切換或混用多個資料來源。

---

## 4. 決策理由

### 為什麼選擇此方案

1. **$0 預算最佳解**：GitHub Actions 免費額度（2000 min/月）對每日一次爬蟲綽綽有餘
2. **Python 爬蟲生態成熟**：`requests` + `BeautifulSoup` / `Playwright` 可應付 Epic Games SPA 頁面
3. **Source 介面設計**：預留擴充點，未來加 API 或其他爬蟲只需新增一個 Source class

### 為什麼放棄其他方案

- **Cloudflare Workers**：免費方案的 CPU 時間限制（30ms）無法勝任 Epic Games 頁面爬取
- **本地排程**：需要 24h 開機設備，與「免維運、零成本」目標不符

---

## 5. 行動計畫

### 技術棧

| 層級 | 技術 | 備註 |
|------|------|------|
| 語言 | Python 3.11+ | |
| 爬蟲 | `requests` + `BeautifulSoup4` | 若 SPA 頁面再加 `Playwright` |
| 通知 | Telegram Bot API（直接 HTTP POST） | 輕量無需套件 |
| 排程 | GitHub Actions `.github/workflows/daily_notify.yml` | Cron: `0 2 * * *`（UTC 02:00 = TST 10:00） |
| 狀態追蹤 | JSON 檔案（`data/sent_deals.json`） | Git 版控 |
| 版控 | GitHub | |

### 架構概覽

```
src/
├── main.py                   # 入口腳本
├── engine.py                 # 排程引擎 — 調度 Source → Tracker → Notifier
├── notifier.py               # Telegram 通知
├── tracker.py                # 已通知記錄管理 (JSON)
└── sources/
    ├── __init__.py
    ├── base.py               # BaseSource (ABC) + Deal dataclass
    └── epic_free.py          # Epic Games 爬蟲實作
```

### 初期任務

| 優先級 | 任務 | 說明 |
|--------|------|------|
| P0 | 建立專案骨架 | 目錄結構、`requirements.txt` |
| P0 | Telegram Bot 建立 | 透過 @BotFather 取得 Token |
| P0 | Source 抽象介面 | `BaseSource` + `Deal` dataclass |
| P0 | EpicFreeSource 實作 | 爬取 Epic Games 限免頁面 |
| P0 | Tracker 實作 | JSON 讀寫 + 去重邏輯 |
| P0 | Notifier 實作 | Telegram Bot API 發送 |
| P0 | Engine 實作 | 完整調度流程 |
| P0 | GitHub Actions 排程 | Cron 設定 + Secrets |
| P1 | 通知訊息美化 | 圖片、按鈕、格式化 |
| P1 | 錯誤通知機制 | 爬蟲/通知失敗時警示 |
| P2 | 支援多來源 | 擴充 Source 實作 |

### 有待驗證的項目 (Spike)

- Epic Games 頁面是 SSR 還是 CSR（決定是否需要 Playwright）
- GitHub Actions 對 Playwright 的支援與快取策略

---

## 6. BDD 測試腳本

依據以上架構，已產出 4 份 Gherkin Feature 檔案：

| Feature | 檔案 | 情境數 |
|---------|------|--------|
| 🕷️ Epic 爬蟲來源 | `features/epic_free_crawler.feature` | 8 |
| 📢 Telegram 通知 | `features/epic_free_notification.feature` | 7 |
| 📋 已通知記錄管理 | `features/epic_free_tracker.feature` | 7 |
| ⚙️ 排程引擎 | `features/epic_free_engine.feature` | 8 |

---

## 7. 風險登錄

| 風險 | 可能性 | 影響 | 緩解措施 |
|------|--------|------|---------|
| Epic Games 頁面結構變動 | 中 | 高 | 爬蟲加上異常偵測 alert |
| Epic 加入反爬機制 | 低 | 高 | 使用 Playwright 模擬瀏覽器 |
| GitHub Actions 用量超額 | 低 | 低 | 一天一次消耗極少 |
| JSON 檔案衝突（多人） | 低 | 低 | 個人專案無此問題 |

---

## 📝 決策後續

- 本文件已存至 `docs/tech-decision-福利好康TG通知-2026-07-21.md`
- BDD 測試腳本存於 `features/` 目錄
- 下一步：開始實作程式碼
