@epic-free @tracker @dedup @p0
Feature: 已通知記錄管理（Tracker）
  作為一個福利好康通知系統
  我希望能夠記錄已通知過的遊戲，避免重複發送
  以便使用者只收到新的限免資訊

  Background:
    Given Tracker 已初始化
    And JSON 儲存檔案路徑為 "data/sent_deals.json"

  @smoke @happy-path @p0
  Scenario: 初次執行，無任何記錄
    Given "data/sent_deals.json" 不存在
    When Tracker 讀取已通知記錄
    Then 回傳空集合 set()
    And 系統可正常新增第一筆記錄

  @happy-path @p0
  Scenario: 過濾出尚未通知的新遊戲
    Given 已通知過的遊戲 source_id 為 ["epic_free_game-a", "epic_free_game-b"]
    And 本次爬取回傳 3 筆 Deal
      | source_id          | title |
      | epic_free_game-a   | 遊戲A |
      | epic_free_game-b   | 遊戲B |
      | epic_free_game-c   | 遊戲C |
    When Tracker 執行 filter_new([deal_A, deal_B, deal_C])
    Then 回傳 1 筆新遊戲 [deal_C]
    And 排除已通知過的 game_a 與 game_b

  @happy-path @p1
  Scenario: 通知成功後標記為已通知
    Given 一筆新 Deal（game_c）
    When Tracker 執行 mark_sent(deal_c)
    Then "data/sent_deals.json" 新增一筆記錄
    | source_id          | notified_at              |
    | epic_free_game-c   | 2026-07-21T10:00:00Z     |
    And 下次 filter_new 會排除 game_c

  @error-handling @p1
  Scenario: JSON 檔案損毀
    Given "data/sent_deals.json" 內容為無效 JSON
    When Tracker 讀取已通知記錄
    Then Tracker 不拋出例外
    And 視為空集合處理
    And 系統記錄警告日誌 "sent_deals.json 損毀，已重置"

  @error-handling @p1
  Scenario: 寫入 JSON 時發生磁碟空間不足
    Given 磁碟空間不足
    When Tracker 執行 mark_sent(deal)
    Then Tracker 拋出 StorageError 例外
    And 錯誤訊息包含 "寫入檔案失敗：磁碟空間不足"
    And 系統維持上一次成功寫入的記錄不變

  @edge-case @p2
  Scenario: 同一遊戲在不同週期再次限免
    Given "epic_free_game-a" 已於 2026-06-01 通知過
    When 本次爬取再次包含 "epic_free_game-a"（新的限免週期）
    Then filter_new 判斷為新遊戲（因為 end_date 不同）
    And 再次通知使用者

  @edge-case @p2
  Scenario: 大量記錄時的讀寫效能
    Given "data/sent_deals.json" 已累積 10000 筆記錄
    When Tracker 執行 filter_new(1 筆新 Deal)
    Then 處理時間不超過 1 秒
    And filter_new 正確判斷該 Deal 為新遊戲
