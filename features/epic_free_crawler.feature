@epic-free @source @crawler @p0
Feature: Epic Free 爬蟲來源
  作為一個福利好康通知系統
  我希望能夠從 Epic Games 商店抓取限時免費遊戲資訊
  以便後續發送通知給使用者

  Background:
    Given 系統已初始化 EpicFreeSource
    And Epic Games 商店頁面可正常存取
    And 已記錄上次通知的遊戲清單為空

  @smoke @happy-path @p0
  Scenario: 成功爬取當期限免遊戲列表
    Given Epic Games 商店有 2 款限時免費遊戲
      | 遊戲名稱       | 原價   | 截止日期   |
      | 遊戲 A        | NT$599 | 2026-07-28 |
      | 遊戲 B        | NT$399 | 2026-08-04 |
    When EpicFreeSource 執行 fetch_deals()
    Then 回傳 2 筆 Deal 物件
    And 每筆 Deal 包含 title、url、source_id、end_date 欄位
    And source_id 格式為 "epic_free_{遊戲唯一識別碼}"
    And source 欄位值為 "epic_free"

  @happy-path @p1
  Scenario: 爬取結果包含完整遊戲資訊
    Given Epic Games 商店有一款限免遊戲 "遊戲 A"
    When EpicFreeSource 執行 fetch_deals()
    Then 回傳的 Deal 包含以下資訊
      | 欄位          | 值                          |
      | title         | 遊戲 A                      |
      | description   | 這是一款精彩的動作冒險遊戲    |
      | url           | https://store.epicgames.com/... |
      | image_url     | https://.../cover.jpg        |
      | source        | epic_free                   |
      | source_id     | epic_free_game-a-20260728   |
      | end_date      | 2026-07-28                  |

  @error-handling @p0
  Scenario: Epic Games 商店頁面無法存取
    Given Epic Games 商店回傳 HTTP 500 錯誤
    When EpicFreeSource 執行 fetch_deals()
    Then 系統拋出 SourceConnectionError 例外
    And 錯誤訊息包含 "無法連線至 Epic Games 商店"
    And 不影響其他 Source 的執行

  @error-handling @p1
  Scenario: 頁面結構變動導致爬蟲失敗
    Given Epic Games 商店頁面 HTML 結構與預期不符
    When EpicFreeSource 執行 fetch_deals()
    Then 系統拋出 ParseError 例外
    And 錯誤訊息包含 "解析頁面結構失敗"
    And 系統記錄完整 HTML 片段以便除錯

  @error-handling @p1
  Scenario: 爬取結果為空（無限免）
    Given Epic Games 商店目前沒有任何限時免費遊戲
    When EpicFreeSource 執行 fetch_deals()
    Then 回傳空列表 []
    And 不回傳任何 Deal 物件
    And 不發送任何通知

  @edge-case @p2
  Scenario: 單一遊戲有多個語言版本
    Given Epic Games 商店一款遊戲支援多國語言
    When EpicFreeSource 執行 fetch_deals()
    Then 只回傳 1 筆 Deal（不去重複）
    And 該 Deal 的 description 包含支援語言資訊

  @edge-case @p2
  Scenario: 遊戲截止日期為跨日邊界
    Given 限免遊戲截止日期為 UTC 23:59
    When EpicFreeSource 執行 fetch_deals()
    Then Deal 的 end_date 正確轉換為 ISO 格式 "2026-07-28T23:59:00Z"

  @edge-case @p2
  Scenario: 爬蟲遭遇反爬機制（CAPTCHA）
    Given Epic Games 商店顯示 CAPTCHA 驗證頁面
    When EpicFreeSource 執行 fetch_deals()
    Then 系統拋出 AntiScrapingDetected 例外
    And 錯誤訊息包含 "偵測到反爬蟲機制"
    And 觸發管理員警示通知
