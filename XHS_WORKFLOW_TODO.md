# XHS (小红书) Workflow — Manual Setup Checklist

> Last updated: 2026-03-12

---

## 1. Log in to XHS ✅ DONE

- [x] SSH into the server as root
- [x] Run the login tool: `cd /root/xiaohongshu-mcp && ./xiaohongshu-login-linux-amd64`
- [x] Scan QR code + SMS verification (code 121777)
- [x] Verify `cookies.json` created: `/root/xiaohongshu-mcp/cookies.json` (4225 bytes)
- [x] Restart MCP service: `sudo systemctl restart xhs-mcp`
- [x] Verify MCP responds: `xiaohongshu-mcp v2.0.0` on port `18060`

---

## 2. Set up `MATON_API_KEY` (for Notion access) ✅ DONE

The Notion skill requires `MATON_API_KEY` from [maton.ai](https://maton.ai).

- [x] Sign up / log in at <https://maton.ai>
- [x] Connect your Notion workspace to Maton (OAuth flow)
- [x] Copy your `MATON_API_KEY`
- [x] Add it to the OpenClaw environment:
  - Set via `openclaw config set env.MATON_API_KEY` → saved in `/root/.openclaw/openclaw.json`
  - Also written to `/root/.openclaw/.env` as backup
- [x] Restart OpenClaw gateway (verified `MATON_API_KEY` in process env)
- [x] Verify Notion access works (confirmed via Maton API: search returns pages and databases)

---

## 3. Create Notion Databases ✅ DONE

All 4 databases created via Maton API under the **XHS Workflow** parent page.

### 3a. XHS Content Calendar ✅
- [x] Created: `88d3d578-b173-487b-9ef9-be32461f91eb`
- Columns: Title, Topic, Category (刚需购房/租房攻略/预算规划/房东指南/首次买房/区域分析), Status (planned/drafted/approved/posted), Platform (xiaohongshu), ScheduledDate, PostURL

### 3b. XHS Post Drafts ✅
- [x] Created: `19e276fc-7e19-4dc3-ba09-29294e06678f`
- Columns: Title, Body, Hashtags, CoverPath, ApprovalStatus (draft/pending_review/approved/rejected), ApprovedBy, PublishedAt, FeedID, XsecToken

### 3c. XHS Engagement Logs ✅
- [x] Created: `b4900809-d714-426e-b6fd-f24a25d2c9f8`
- Columns: FeedID (title), CommentID, UserNickname, CommentText, EngagementLevel (browsing/curious/interested/potential_buyer/potential_renter/potential_seller), ReplySent (checkbox), ReplyText, ClassifiedAt

### 3d. Social Leads ✅
- [x] Created: `6ed3071e-ccac-42c0-998f-bac64f56ad93`
- Columns: Name, Platform (xiaohongshu), SourcePost, Intent (buy/rent/sell/landlord), Budget, Area, PropertyType, Rooms, WeChatStatus (wechat_requested/wechat_added/waiting_for_wechat), CRMStage
- Note: `LinkedClient` relation skipped (requires an existing Clients db to link to)

- [x] Database IDs noted above

---

## 3e. 房源列表 Property Listings ✅ NEW

- [x] Created: `081e67fe-00f9-446a-8a4d-9ccaf5af4df1`
- Columns: Name, PropertyType, Area, District, Price, PriceUnit, Rooms, Size, Highlights, ImagePaths, XHSPostStatus (new/draft_ready/posted/failed), XHSPostURL, PostedAt, AddedAt
- 2 example listings added (Wangjing 2BR + Zhongguancun rental)
- Sample cover images generated at `/root/property-images/`

### xhs-property-post skill ✅

- [x] Skill installed: `/root/.openclaw/workspace/skills/xhs-property-post/SKILL.md`
- [x] Status: `ready` in `openclaw skills list`
- Reads `XHSPostStatus=new` listings → generates XHS content → publishes via MCP → updates Notion
- **QQ trigger**: send "发房源" or "推广新房源"
- **Cron**: daily 17:00 Beijing time (job `daily-property-post`, ID `bb6a821a-3008-475c-ac0d-4d3b92dafa2a`)
- Anti-spam: max 2 posts per run, 60s interval between posts

---

## 4. Set up Attio CRM API Key

- [ ] Get your API key from <https://app.attio.com> → Settings → API
- [ ] Add `ATTIO_API_KEY=your_key` to the OpenClaw environment (same method as step 2)
- [ ] Create custom fields in Attio (on People/Deals objects):
  - `wechat` (text)
  - `intent_type` (select)
  - `preferred_area` (text)
- [ ] Restart OpenClaw

---

## 5. (Optional) Set up Feishu Calendar

For lead-to-viewing scheduling to work:

- [ ] Check the `feishu-calendar` skill requirements
- [ ] Add any needed Feishu credentials/env vars to OpenClaw environment
- [ ] Restart OpenClaw

---

## 6. (Optional) Set up Cover Image AI Generation

The rednote skill can auto-generate XHS cover images. Set **one** of these:

- [ ] `GEMINI_API_KEY` (Google) **or**
- [ ] `IMG_API_KEY` **or**
- [ ] `HUNYUAN_SECRET_ID` + `HUNYUAN_SECRET_KEY` (Tencent)

If skipped, you can still create/upload cover images manually.

---

## 7. Restart & Validate End-to-End

- [ ] `sudo openclaw restart`
- [ ] Test topic research:
  > "帮我研究一个小红书选题，关于朝阳区刚需两居"
- [ ] Verify topic research returns results
- [ ] Ask to generate a draft post → check it appears in Notion **XHS Post Drafts**
- [ ] Manually set `ApprovalStatus` → `approved` in Notion
- [ ] Ask the bot to publish → verify it appears on XHS
- [ ] Test engagement monitoring:
  > "检查小红书互动"
- [ ] Verify leads are captured in Notion **Social Leads** and Attio CRM

---

## 8. Ongoing Maintenance

- [ ] **XHS cookies expire** — re-login periodically
  ```bash
  sudo bash -c 'export DISPLAY=:99 && cd /root/xiaohongshu-mcp && ./xiaohongshu-login-linux-amd64'
  # Then: sudo systemctl restart xhs-mcp
  ```
- [ ] Set a weekly reminder to check login status
- [ ] If bot reports MCP errors or heartbeat shows "MCP未就绪", re-run login
- [ ] (Optional) Set up a cron job to hit `check_login_status` and alert you

---

### Priority

| Priority | Steps | Why |
|---|---|---|
| **Blocker** | 1 ✅, 2 ✅, 3 ✅ | Nothing works without XHS login + Notion |
| **Important** | 4 | Leads won't persist to CRM without Attio |
| **Nice-to-have** | 5, 6 | Scheduling & auto cover images |
| **Validation** | 7 | Confirm everything works end-to-end |
| **Ongoing** | 8 | Keep the system running |
