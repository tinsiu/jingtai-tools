#!/usr/bin/env python3
"""format_digest.py — 把 4 个 fetcher 输出合并成单一 Markdown digest"""

import os
import sys
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path("output")


def read_section(name: str) -> str:
    p = OUTPUT_DIR / f"{name}.md"
    if not p.exists():
        return f"<!-- {name}: no output -->"
    return p.read_text(encoding="utf-8")


def main() -> int:
    OUTPUT_DIR.mkdir(exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d %H:%M CST")

    digest = f"""# 🤖 AI 工具日报 — {today}

> 自动汇总 GitHub Trending / Product Hunt / Hacker News / awesome-*  
> 来自 JingTai Tools Curator (GitHub Action)

---

## 📈 GitHub Trending

{read_section("github_trending")}

---

## 🚀 Product Hunt (AI)

{read_section("producthunt")}

---

## 📰 Hacker News (Show HN + AI)

{read_section("hackernews")}

---

## ⭐ awesome-* 更新

{read_section("awesome")}

---

## 📥 后续流程

1. ECS / WSL cron 每 4 小时拉取本邮件
2. LLM 评分 1-5 (基于 JingTai 业务相关性)
3. 评分 ≥4 → 推飞书；评分 3 → 入库；评分 ≤2 → 仅日志
4. 飞书每日 09:00 CST 报告 Top 5 推荐

---

*JingTai Tools Curator · Tom 的 AI 工具发现系统*
"""

    out_path = OUTPUT_DIR / "digest.md"
    out_path.write_text(digest, encoding="utf-8")
    print(f"✅ Digest written to {out_path} ({len(digest)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
