---
name: xhs-comment-reply
description: |
  小红书评论自动回复 — 定时检查已发布笔记的评论，自动回复咨询类评论并记录到 Notion。
  当用户提到以下关键词时激活：回复评论、处理小红书评论、xhs评论、自动回复评论。
metadata:
  author: workspace
  version: "1.0"
  openclaw:
    emoji: 💬
    requires:
      env:
        - MATON_API_KEY
      anyBins:
        - curl
        - python3
---

# 小红书评论自动回复

定时检查已发布房源笔记的评论，识别咨询类评论并**直接回复**（无需向用户确认）。使用固定话术「有需要可以私聊我～」引导私聊，**不调用 LLM 生成回复**，节省 token。已回复记录写入 Notion Engagement Logs 防止重复。

## 配置常量

NOTION_DB_ID = 081e67fe-00f9-446a-8a4d-9ccaf5af4df1
ENGAGEMENT_DB_ID = b4900809-d714-426e-b6fd-f24a25d2c9f8
MCP_URL = http://localhost:18060/mcp

## 触发方式

- 定时：每 4 小时 (10:00/14:00/18:00/22:00 北京时间)
- 手动：企微/QQ 发 "回复评论"、"处理小红书评论"

## 回复规则

- **固定话术**：`有需要可以私聊我～`（统一使用，不调用 LLM）
- **需回复**：正文含 私聊、多少钱、求推荐、有兴趣、怎么联系 等关键词（关键词匹配，无需 LLM）
- **不回复**：已回复过、纯表情、广告、负面言论
- **限制**：每帖最多 5 条/次，总最多 15 条/次，间隔 30 秒

## 执行流程

1. 初始化 MCP Session (Mcp-Session-Id)
2. 查询 Notion 房源表 XHSPostStatus=posted 且有 XHSPostURL 的记录
3. 对每篇帖子调用 get_feed_detail 获取评论
4. 用**关键词匹配**过滤待回复（查 Engagement Logs 去重；正文含 私聊、多少钱、求推荐、有兴趣、怎么联系 等）— **无需 LLM**
5. **直接回复**：对每条待回复评论立即发送，**无需向用户确认**
6. 固定回复：`@评论者昵称 有需要可以私聊我～`（不调用 LLM 生成）
7. 使用 post_comment_to_feed 发送（勿用 reply_comment_in_feed，headless 下易超时）
8. 写入 Engagement Logs 防重复
9. 汇报：检查 X 篇/发现 Y 条/回复 Z 条

## MCP 调用

get_feed_detail: feed_id, xsec_token, load_all_comments=true
post_comment_to_feed: feed_id, xsec_token, content（格式：@评论者昵称 有需要可以私聊我～）
