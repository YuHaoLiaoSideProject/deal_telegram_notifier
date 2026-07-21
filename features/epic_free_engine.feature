@epic-free @engine @orchestration @p0
Feature: 排程引擎（Engine）
  作為一個福利好康通知系統
  我希望 Engine 能夠協調 Source、Tracker、Notifier 完成每日通知流程
  以便整個流程自動化運作

  Background:
    Given Engine 已初始化
    And 已註冊 EpicFreeSource 作為資料來源
    And Tracker 與 Notifier 已正確注入

  @smoke @happy-path @p0
  Scenario: 完整每日通知流程（有新遊戲）
    Given EpicFreeSource 回傳 2 筆 Deal（game_a, game_b）
    And game_b 尚未被通知過
    And game_a 已被通知過
    When Engine 執行 run()
    Then Engine 依序執行：
      | 步驟             | 順序 |
      | 呼叫所有 Source  | 1    |
      | 合併 Deal 列表   | 2    |
      | Tracker 過濾新遊戲 | 3    |
      | Notifier 發送通知 | 4    |
      | Tracker 標記已通知 | 5    |
    And Notifier 只發送 game_b 的通知
    And Tracker 記錄 game_b 為已通知

  @happy-path @p1
  Scenario: 完整每日通知流程（無新遊戲）
    Given EpicFreeSource 回傳 2 筆 Deal
    And 所有 Deal 都已被通知過
    When Engine 執行 run()
    Then Engine 不呼叫 Notifier
    And 記錄日誌 "今日無新限免遊戲"
    And 流程正常結束

  @error-handling @p0
  Scenario: 某個 Source 爬取失敗，不影響整體流程
    Given EpicFreeSource 拋出 SourceConnectionError
    And 已註冊第二個 Source（SteamFreeSource）回傳正常
    When Engine 執行 run()
    Then Engine 記錄 EpicFreeSource 失敗
    And 繼續執行 SteamFreeSource
    And 發送 Steam 限免通知
    And 最終回報摘要：1 個來源成功，1 個來源失敗

  @error-handling @p1
  Scenario: 所有 Source 都失敗
    Given 所有已註冊 Source 都拋出例外
    When Engine 執行 run()
    Then Engine 不發送任何通知
    And 記錄錯誤日誌 "所有資料來源皆無法取得"
    And 觸發管理員警示

  @error-handling @p2
  Scenario: Tracker 寫入失敗時不影響通知
    Given 有新遊戲 game_b
    And Tracker 執行 mark_sent(game_b) 拋出 StorageError
    When Engine 執行 run()
    Then Notifier 仍成功發送 game_b 的通知
    And Engine 記錄 "標記已通知失敗，需手動處理"
    And 下次 run() 會再次嘗試標記

  @edge-case @p2
  Scenario: GitHub Actions 時區與 Cron 設定
    Given 排程設為 "0 2 * * *"（UTC 02:00）
    When 台北時間為每日 10:00
    Then Engine 在 UTC 02:00 被觸發執行
    And 通知訊息顯示的日期以台北時區為準

  @edge-case @p2
  Scenario: 同一天觸發多次（重複執行保護）
    Given Engine 已於今日 10:00 執行過
    And 已成功通知並標記
    When Engine 在今日 18:00 再次被觸發
    Then Engine 過濾後發現無新遊戲
    And 不發送重複通知
    And 記錄 "今日已執行過，跳過"

  @edge-case @p1
  Scenario: 通知訊息格式化
    Given 有一筆新 Deal（遊戲 A，截止於 2026-07-28）
    When Engine 格式化通知訊息
    Then 訊息格式如下：
      """
      🎮 本期限時免費遊戲

      📌 遊戲 A
      📅 截止：2026-07-28
      🔗 https://store.epicgames.com/...

      #EpicGames #限時免費
      """
