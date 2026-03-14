# 小红书 MCP 登录稳定方案

## 问题根因

- 扫码后需**二次验证**（短信/设备安全码），MCP 无法输入验证码
- `cookies.json` 未被更新，`check_login_status` 一直返回未登录

## 方案一：本地登录 → 拷贝 cookies（官方推荐，最稳定）

**适用**：有 Mac / Windows / 带桌面 Linux 的电脑

### 步骤

1. **下载登录工具**（与 MCP 同版本，从 xiaohongshu-mcp releases）
   - Linux: `xiaohongshu-login-linux-amd64`
   - Mac Intel: `xiaohongshu-login-darwin-amd64`
   - Mac M1/M2: `xiaohongshu-login-darwin-arm64`
   - Windows: `xiaohongshu-login-windows-amd64.exe`

2. **在本机运行**：`./xiaohongshu-login-linux-amd64`（或对应平台）

3. **完成登录**：扫码 → 收验证码 → 在窗口输入验证码 → 登录成功

4. **上传 cookies**：`scp cookies.json root@YOUR_SERVER:/root/xiaohongshu-mcp/`

5. **重启 MCP**：`ssh root@YOUR_SERVER "systemctl restart xhs-mcp"`

---

## 方案二：浏览器 Cookie + jobsonlook MCP

[jobsonlook/xhs-mcp](https://github.com/jobsonlook/xhs-mcp) 纯 HTTP 请求，无 Playwright。配置 `XHS_COOKIE` 即可：

1. 在浏览器登录 xiaohongshu.com
2. F12 → Application → Cookies，复制 cookie 字符串（含 a1、web_session、id_token、webId、sec_poison_id、xsecappid 等）
3. 运行 `bash /home/ubuntu/xhs-jobsonlook-setup.sh` 安装并启动 jobsonlook（通过 mcp-proxy 暴露端口 18060）
4. 或手动：`XHS_COOKIE="name1=val1; name2=val2; ..." npx mcp-proxy --port 18060 -- uvx --from jobson-xhs-mcp xhs-mcp`

---

## 方案三：服务器 VNC 远程桌面

无本地桌面时，在服务器装 VNC，远程登录后运行 `xiaohongshu-login-linux-amd64`，完成扫码和验证后复制 cookies.json 到 MCP 目录。

---

## Cookie 有效期

通常 1–2 周失效，需按方案一重新登录。
