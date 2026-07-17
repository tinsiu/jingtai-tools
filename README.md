# 🤖 JingTai AI Tools Curator

**自动收集 GitHub / Product Hunt / Hacker News 上的 AI 工具，AI 评估相关性，邮件汇总到 Tom，飞书每日报告。**

> 这是为精泰（JingTai Heat Transfers）业务定制的内部工具发现系统。

---

## 🏗️ 架构

```
GitHub Action (每 6 小时)
  ├─ 抓取 GitHub Trending (AI/Automation/Agent)
  ├─ 抓取 Product Hunt (AI Top)
  ├─ 抓取 Hacker News (Show HN + AI)
  └─ 抓取 awesome-* 列表更新
       ↓
  邮件发到 tom@mildign.com (subject: [TOOL-FEED])
       ↓
Gmail 过滤规则 (from:curator + subject:[TOOL-FEED]) → AI-Tools/Inbox 文件夹
       ↓
ECS / WSL 端 cron (每 4 小时跑一次)
  ├─ IMAP 拉 AI-Tools/Inbox 未读
  ├─ LLM 评分 (1-5)
  ├─ 去重 + 入 tool_registry 表
  └─ 评分 ≥4 推飞书日报
       ↓
飞书每日 9:00 报告 (Top 5 推荐 + 累计统计)
```

---

## ⚙️ 配置

### GitHub Secrets (在 repo Settings → Secrets 配置)

| Secret 名 | 含义 | 例子 |
|-----------|------|------|
| `SMTP_USER` | 发件邮箱 | `tom@mildign.com` |
| `SMTP_PASS` | Gmail 应用密码 | `rwms izir livl khjr` |
| `FEISHU_WEBHOOK` | 飞书机器人 webhook | (Tom 私人持有) |

> ⚠️ **Tom 改密码后记得更新 SMTP_PASS** — Gmail 应用密码不是登录密码，需要去 https://myaccount.google.com/apppasswords 重新生成

---

## 🔄 触发规则

GitHub Action 每 6 小时跑一次（也可手动 `workflow_dispatch`）。

邮箱收到后，ECS 端 cron 会在 4 小时内处理完。

飞书每日 09:00 CST 推送昨日汇总。

---

## 📂 文件结构

```
jingtai-tools/
├── README.md                           # 你正在看的
├── .github/
│   └── workflows/
│       └── curator.yml                 # GitHub Action 主工作流
└── scripts/
    ├── fetch_github_trending.py        # GitHub Trending 抓取
    ├── fetch_producthunt.py            # Product Hunt 抓取
    ├── fetch_hackernews.py             # HN Show 抓取
    ├── fetch_awesome.py                # awesome-* 列表更新
    └── format_digest.py                # Markdown 汇总
```

---

## 📊 评分规则

AI 用 JingTai 业务相关性 + 工具成熟度评估（1-5 分）：

| 分 | 含义 | 行动 |
|----|------|------|
| 5 | 直接相关 + 高成熟 | 立即评估试用 |
| 4 | 相关 / 高潜力 | 推飞书，等 Tom 决策 |
| 3 | 观望 | 入库但不推 |
| 2 | 弱相关 | 仅日志，不入库 |
| 1 | 不相关 | 跳过 |

---

## 🔗 相关链接

- **GitHub**: https://github.com/tinsiu/jingtai-tools
- **业务站点**: https://mildign.com
- **精泰产品**: Flock / DTF / Screen Print / Rhinestone 热转印

---

*维护：Tony (AI 调度) · Tom (决策)*
