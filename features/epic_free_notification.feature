@epic-free @notification @telegram @p0
Feature: Telegram 通知發送
  作為一個福利好康通知系統
  我希望能夠透過 Telegram Bot 發送限免遊戲通知給使用者
  以便使用者即時獲取優惠資訊

  Background:
    Given Telegram Bot Token 已正確設定
    And 接收通知的 Chat ID 已正確設定
    And Notifier 已初始化

  @smoke @happy-path @p0
  Scenario: 成功發送單一遊戲通知
    Given 有一筆 Deal 物件
      | 欄位     | 值                          |
      | title    | 遊戲 A                      |
      | url      | https://store.epicgames.com/... |
      | end_date | 2026-07-28                  |
    When Notifier 呼叫 send(deal)
    Then Telegram Bot API 回傳 HTTP 200
    And 使用者收到一則訊息，內容包含
      | 項目     | 內容                        |
      | 標題     | 🎮 遊戲 A                   |
      | 說明     | Epic Games 本期限時免費！    |
      | 截止日期 | 2026-07-28                  |
      | 連結     | https://store.epicgames.com/... |
    And 通知訊息包含「立即領取」按鈕

  @happy-path @p1
  Scenario: 成功發送多筆遊戲通知（合併一則）
    Given 有 3 筆 Deal 物件（遊戲 A、遊戲 B、遊戲 C）
    When Notifier 呼叫 send_batch([deal_A, deal_B, deal_C])
    Then Telegram Bot API 回傳 HTTP 200
    And 使用者收到一則合併訊息
    And 訊息列出 3 款遊戲的名稱與截止日期
    And 不發送 3 則獨立訊息

  @error-handling @p0
  Scenario: Telegram Bot Token 無效
    Given Telegram Bot Token 設為 "INVALID_TOKEN"
    When Notifier 呼叫 send(deal)
    Then Notifier 拋出 NotificationError 例外
    And 錯誤訊息包含 "Unauthorized：Bot Token 無效"
    And 系統記錄錯誤日誌

  @error-handling @p1
  Scenario: 發送訊息超過 Telegram 字數限制
    Given 一筆 Deal 的 description 長度超過 4096 字元
    When Notifier 呼叫 send(deal)
    Then Notifier 自動截斷訊息至 4096 字元
    And 在訊息結尾附加「…（內容過長已截斷）」
    And 不會發送空訊息

  @error-handling @p1
  Scenario: Telegram API 暫時不可用
    Given Telegram Bot API 回傳 HTTP 429（Rate Limit）
    When Notifier 呼叫 send(deal)
    Then Notifier 自動重試最多 3 次
    And 每次重試間隔遞增（exponential backoff）
    And 若 3 次重試仍失敗，拋出 NotificationError

  @edge-case @p2
  Scenario: 通知訊息包含特殊字元
    Given 遊戲名稱包含 "®"、"™"、"🎮" 等特殊字元
    When Notifier 呼叫 send(deal)
    Then Telegram 訊息正確顯示所有特殊字元
    And 不發生編碼錯誤

  @edge-case @p2
  Scenario: Chat ID 無效或已被封鎖
    Given Chat ID 對應的使用者已封鎖 Bot
    When Notifier 呼叫 send(deal)
    Then Notifier 拋出 NotificationError
    And 錯誤訊息包含 "chat not found"
    And 系統記錄該 Chat ID 為失效狀態
