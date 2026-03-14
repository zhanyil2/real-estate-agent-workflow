# Project Workflow — Design Brief for Customer-Facing Diagram

> **Purpose**: Provide a complete, structured description of all workflows for an art designer to create an attractive, customer-facing workflow diagram.

---

## Overview

The system has **two main product workflows**:

| Workflow | Target User | Value Proposition |
|----------|-------------|-------------------|
| **Real Estate AI** | 房产经纪人 (Property agents) | "你只管带人看房，剩下的交给 AI" — You focus on showing properties; AI handles everything else |
| **E-commerce Trends** | E-commerce / cross-border sellers | Daily trending product reports delivered to QQ |

Both are orchestrated by **OpenClaw** (AI agent runtime) and share some channels.

---

## 1. Real Estate AI Workflow (Primary)

### 1.1 High-Level Flow (One-Liner for Designer)

**From WeChat groups and Notion → AI processes → Xiaohongshu posts + auto-replies → Leads back to agent**

### 1.2 Actor / Persona

- **经纪人 (Agent)**: Real estate agent, primary user. Uses 企业微信 (WeCom) and QQ.
- **Xiaohongshu users**: Potential leads who comment on property posts.
- **Group members**: Other agents in 房源互通群 who share listings.

### 1.3 Triggers (Entry Points)

| Trigger | Type | Time / Condition | User Action |
|---------|------|------------------|-------------|
| 群聊监控 | 24/7 automatic | Real-time | None — AI monitors all groups |
| 客户找房 | On-demand | When agent asks | Agent says: "找望京三居600万" |
| 发房源 | Manual + Cron | Daily 17:00 or "发房源" | Agent says: "发房源" |
| 回复评论 | Manual + Cron | Every 4h (10/14/18/22) or "回复评论" | Agent says: "回复评论" |
| 小红书找群 | Weekly | Mon and Thu 10:00 | None — automatic |

### 1.4 Step-by-Step Flows

#### Flow A: 群聊房源监控 (Group Chat Listing Monitor)

- **Input**: Group messages (e.g., "望京西园四区 2室1厅 89平 580万")
- **Flow**: 房源互通群 1–N → OpenClaw → AI parses listings → deduplicate → Notion 房源库
- **Output**: Structured listing in Notion (price, area, rooms, location)
- **Frequency**: Real-time, 24/7

#### Flow B: 客户找房匹配 (Customer Property Search)

- **Input**: Agent says "找望京两居500万" in 企微
- **Flow**: OpenClaw → Search Notion 房源库
  - If match: Return 3–5 recommended listings
  - If no match: AI broadcasts request to 5 groups → Someone replies → AI extracts listing → Saves to Notion → Notifies agent

#### Flow C: 小红书自动发帖 (XHS Auto-Post)

- **Input**: Notion 房源库 with XHSPostStatus=new
- **Flow**: OpenClaw → xhs-property-post skill → AI generates copy (title, 600–800 chars, cover) → xiaohongshu-mcp publishes → Update Notion (posted, URL)
- **Trigger**: Daily 17:00 or "发房源"
- **Anti-spam**: Max 2 posts/day, 60s interval

#### Flow D: 小红书评论自动回复 (XHS Comment Auto-Reply)

- **Input**: Cron (10/14/18/22) or "回复评论"
- **Flow**: Notion posted listings → xiaohongshu-mcp get comments → Keyword filter (私聊/多少钱/求推荐/有兴趣/怎么联系) → post_comment_to_feed "@用户 有需要可以私聊我～" → Notion Engagement Logs (dedup)
- **Limit**: Max 5 per post per run, 30s interval

#### Flow E: 小红书找群 (XHS Group Discovery)

- **Flow**: Cron Mon/Thu 10:00 → search_feeds "房产经纪人群" → AI identifies group invite posts → Like + comment → Extract join method → Save to Notion for agent to join

### 1.5 Data Stores (Notion)

- Property Listings (房源列表): All listings; XHSPostStatus, XHSPostURL
- XHS Content Calendar: Content planning
- XHS Post Drafts: Drafts before publish
- XHS Engagement Logs: Comment replies (deduplication)
- Social Leads: Qualified leads from comments

### 1.6 External Integrations

- 企业微信 (WeCom): Main chat; commands, group monitoring
- QQ Bot: Backup trigger
- Xiaohongshu MCP: Publish, comments, search
- Notion (Maton API): Central data store
- Attio CRM: (Planned) Lead sync

---

## 2. E-commerce Trends Workflow (Secondary)

### 2.1 High-Level Flow

**Google Trends / LLM → Collect keywords → LLM analysis → Report → QQ push**

### 2.2 Triggers

- Cron: Daily 08:00
- Manual: `python daily_job.py --now`

### 2.3 Step-by-Step Flow

1. **Collect**: Google Trends (US/GB/JP/SG) or LLM generates → trends_collector.py → data/trends/*.json
2. **Analyze**: product_opportunity.py (LLM) → data/opportunities/*.json
3. **Report**: daily_report.py → Top 10 opportunities report
4. **Notify**: send_report.py → OpenClaw Gateway → QQ user (fallback: data/unsent_reports/)

### 2.4 Output

- Report: Top N product opportunities (demand score, sourcing difficulty, profit potential)
- Delivery: QQ via OpenClaw API

---

## 3. Diagram Design Suggestions

### 3.1 Layout Ideas

1. **Hub-and-spoke**: OpenClaw in center; WeCom, QQ, Notion, Xiaohongshu MCP around it
2. **Two lanes**: Top = Real estate (WeCom → OpenClaw → Notion → XHS); Bottom = E-commerce (Trends → Analysis → Report → QQ)
3. **Timeline**: "Agent's Day" 8:00–20:00 with AI actions at each time

### 3.2 Visual Hierarchy

- **OpenClaw**: Central hub; larger, distinct color
- **User touchpoints** (WeCom, QQ): Rounded; human icon
- **Automated processes**: Dashed borders or gear icon
- **Data stores** (Notion): Database/table icon
- **Cron triggers**: Clock icon + time label
- **Real-time**: Lightning bolt icon

### 3.3 Color Coding

- Real estate: Warm tones (orange/amber)
- E-commerce: Cool tones (blue/teal)
- Triggers: Green (automatic) vs. yellow (manual)

### 3.4 Key Labels (Chinese)

- "24/7 群聊监控"
- "秒级匹配"
- "自动发帖，永不断更"
- "评论自动回复，引导私聊"
- "你只管带人看房"

### 3.5 Icon Suggestions

- Agent: Person with house
- WeChat/QQ: Chat bubble
- Xiaohongshu: Red notebook
- Notion: Blocks/table
- AI: Brain/sparkle
- Cron: Clock
- Leads: Target/handshake

---

## 4. Simplified One-Page ASCII Flow

```
         [企微/QQ] ← Agent
              │
    ┌─────────┼─────────┐
    ▼         ▼         ▼
 群聊监控   找房匹配   发房源/回复评论
    │         │         │
    └─────────┼─────────┘
              ▼
        [OpenClaw] AI 中枢
              │
    ┌─────────┼─────────┐
    ▼         ▼         ▼
 [Notion] [XHS MCP] [LLM]
    │         │
    └─────────┴──→ [小红书] 内容+获客
```

---

## 5. Summary for Designer

**One sentence**: Real estate agents use WeChat/QQ to trigger AI; the system monitors groups, matches properties, auto-posts to Xiaohongshu, and auto-replies to comments — so agents spend time showing properties, not doing admin.

**Two workflows**: 1) Real Estate: WeCom/QQ ↔ OpenClaw ↔ Notion ↔ Xiaohongshu. 2) E-commerce: Trends → Analysis → Report → QQ.

**Key elements**: Central hub (OpenClaw), user channels (WeCom/QQ), data store (Notion), content channel (Xiaohongshu), time triggers (clocks).
