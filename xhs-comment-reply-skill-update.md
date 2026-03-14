---
name: xhs-comment-reply
description: |
  小红书评论自动回复 — 定时检查已发布笔记的评论，自动回复咨询类评论并记录到 Notion。
  当用户提到以下关键词时激活：回复评论、处理小红书评论、xhs评论、自动回复评论。
metadata:
  author: workspace
  version: "1.2"
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

定时检查已发布房源笔记的评论，识别咨询类评论并**直接回复**（无需向用户确认）。使用固定话术引导私聊，**不调用 LLM 生成回复**，节省 token。

**执行原则**：无需询问或确认，发现待回复评论后立即发送固定回复。

## 配置常量

NOTION_DB_ID = 081e67fe-00f9-446a-8a4d-9ccaf5af4df1
ENGAGEMENT_DB_ID = b4900809-d714-426e-b6fd-f24a25d2c9f8
MCP_URL = http://localhost:18060/mcp

## 触发方式

- 定时：每 4 小时 (10:00/14:00/18:00/22:00 北京时间)
- 手动：企微/QQ 发 "回复评论"、"处理小红书评论"
- 指定帖子：如 "回复 帖子北漂3年终于找到✅中关村这个宝藏一居！中的评论"

## ⚠️ 强制规则：@ 回复（必须严格遵守）

**禁止使用 reply_comment_in_feed。** 该工具在 headless/服务器环境下必定失败，会返回「MCP 无法找到评论元素」「评论元素查找超时」。不要尝试该工具，不要有 fallback 到 reply 的逻辑。

**必须且仅使用 post_comment_to_feed** 实现 @ 回复，让对方收到提醒：

- 内容格式：`@评论者昵称 有需要可以私聊我～`（@ 与昵称之间无空格，昵称与内容之间一个空格）
- **固定话术**：所有回复一律使用「有需要可以私聊我～」，不调用 LLM 生成
- 从 get_feed_detail 返回的 comment 中取 user_name 或 nick_name 作为 @ 后的昵称

这样对方会收到 @ 提醒，效果等同楼中楼回复。

## 找帖子的优先级（必须按顺序执行）

1. **Notion 优先**：从用户消息提取帖子标题关键词（如"北漂3年""中关村""一居"），查询 Notion 房源表：
   - 条件：XHSPostStatus=posted
   - 匹配：Name 或 XHSPostTitle 包含关键词
   - 取第一条，读取 XHSFeedId 和 XHSXsecToken
   - 若两者都有，直接使用，跳至「获取评论」步骤

2. **小红书搜索**：若 Notion 无匹配或缺少 XHSXsecToken，用 search_feeds：
   - keyword：从标题提取 2-4 个核心词，如 "中关村 一居" 或 "北漂 中关村"
   - 取第一个结果，用其 id 和 xsecToken

3. **禁止**：不要用 list_feeds 替代 search_feeds 找指定帖子。list_feeds 是推荐流，无法按标题定位。

## 执行流程

1. 从用户消息提取帖子标题（"回复 帖子XXX中的评论" → XXX）
2. 按「找帖子的优先级」获取 feed_id 和 xsec_token
3. 调用 get_feed_detail(feed_id, xsec_token, load_all_comments=true, limit=25)
4. 用**关键词匹配**筛选待回复（非自己、非广告，正文含：私聊、多少钱、求推荐、有兴趣、怎么联系 等）— **无需 LLM**
5. **直接回复**：对每条待回复评论，立即调用 post_comment_to_feed，**无需向用户确认**
6. 固定回复内容：`@评论者昵称 有需要可以私聊我～`（不调用 LLM 生成）
7. 汇报：成功回复 X 条

## 私信回复（当前限制）

当前 xiaohongshu-mcp 不支持私信 API，无法自动回复私信。固定回复「有需要可以私聊我～」即已引导用户私聊，无需额外处理。

## 回复规则

- **固定话术**：`有需要可以私聊我～`（所有评论统一使用，不调用 LLM）
- **需回复**：正文含 私聊、多少钱、求推荐、有兴趣、怎么联系 等关键词（关键词匹配即可，无需 LLM 判断意图）
- **不回复**：已回复过、纯表情、广告、负面言论
- **限制**：每帖最多 5 条/次，间隔 30 秒

## MCP 调用

get_feed_detail: feed_id, xsec_token, load_all_comments=true, limit=25
post_comment_to_feed: feed_id, xsec_token, content（固定格式：@评论者昵称 有需要可以私聊我～）
search_feeds: keyword（用简短关键词，如"中关村 一居"）

## 超时与重试

- **search_feeds**：可能需 1–2 分钟，请耐心等待，勿中断或重启服务
- **get_feed_detail**：若 load_all_comments=true 超时，可重试 load_all_comments=false（更快，评论数可能较少）
- **post_comment_to_feed**：MCP 已配置 headed 模式（Xvfb），评论输入框应能正常渲染
