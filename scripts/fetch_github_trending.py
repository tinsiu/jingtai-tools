#!/usr/bin/env python3
"""fetch_github_trending.py — 抓 GitHub Trending + 多维度信号

筛选维度（不只是 star 数）：
- ⭐ total_stars        累计 star
- 🔺 daily_stars        今日新增 star（GitHub Trending daily 排行）
- 🔺 weekly_stars       本周新增 star（GitHub Trending weekly 排行）
- 🍴 forks               fork 数
- 📅 last_commit_days    最近 commit 距今天数（>180 = 半年没动 = 半弃）
- 🐛 issues              open issues 数
- 📝 desc_len            描述长度（过短 = 不成熟）
- 🔧 language            主语言

评分逻辑（在 main() 里）：
- momentum = (weekly_stars / max(1, total_stars)) × 100 + min(30, daily_stars * 3)
- active_bonus = last_commit_days < 30 ? 20 : (last_commit_days < 90 ? 10 : 0)
- desc_bonus = min(15, desc_len / 8)
- final_score = momentum + active_bonus + desc_bonus
"""

import sys
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone

LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 25
LANGUAGES = ["python", "typescript", "javascript", "rust", "go"]
SINCE_OPTIONS = ["daily", "weekly"]  # 只抓这两档，避免抓 monthly 太慢

GH_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/vnd.github+json",
}


def fetch_trending(language: str = "", since: str = "daily") -> list[dict]:
    """Fetch trending repos for one language + one time window."""
    if language:
        url = f"https://github.com/trending/{language}?since={since}"
    else:
        url = f"https://github.com/trending?since={since}"
    try:
        r = requests.get(url, headers=GH_HEADERS, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"<!-- error fetching {url}: {e} -->", file=sys.stderr)
        return []

    soup = BeautifulSoup(r.text, "lxml")
    repos = []
    for article in soup.select("article.Box-row"):
        try:
            title_link = article.select_one("h2 a")
            if not title_link:
                continue
            path = title_link.get("href", "").strip()
            if not path.startswith("/"):
                continue
            full_name = path.lstrip("/")
            desc_el = article.select_one("p")
            desc = desc_el.get_text(strip=True) if desc_el else ""
            # star 数（带 k/m 后缀的简写）
            stars_el = article.select_one("a[href$='/stargazers']")
            stars = parse_count(stars_el.get_text(strip=True)) if stars_el else 0
            # fork 数
            forks_el = article.select_one("a[href$='/forks']")
            forks = parse_count(forks_el.get_text(strip=True)) if forks_el else 0
            lang_el = article.select_one("[itemprop='programmingLanguage']")
            lang = lang_el.get_text(strip=True) if lang_el else ""
            repos.append({
                "name": full_name,
                "url": f"https://github.com/{full_name}",
                "description": desc,
                "stars": stars,
                "forks": forks,
                "language": lang or language,
                "_since": since,
            })
        except Exception as e:
            print(f"<!-- parse error: {e} -->", file=sys.stderr)
            continue
    return repos


def parse_count(text: str) -> int:
    """Parse '1,234' or '12.5k' or '3.4m' to int."""
    text = text.replace(",", "").strip()
    if not text:
        return 0
    try:
        if text[-1].lower() == "k":
            return int(float(text[:-1]) * 1000)
        if text[-1].lower() == "m":
            return int(float(text[:-1]) * 1_000_000)
        return int(float(text.split()[0]))
    except Exception:
        return 0


def fetch_repo_meta(full_name: str) -> dict:
    """GitHub REST API 拿单个 repo 详情（last commit, open issues, etc.）"""
    url = f"https://api.github.com/repos/{full_name}"
    try:
        r = requests.get(url, headers=GH_HEADERS, timeout=10)
        if r.status_code != 200:
            return {}
        d = r.json()
        pushed_at = d.get("pushed_at", "")
        last_commit_days = None
        if pushed_at:
            try:
                dt = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
                last_commit_days = (datetime.now(timezone.utc) - dt).days
            except Exception:
                pass
        return {
            "stars": d.get("stargazers_count", 0),
            "forks": d.get("forks_count", 0),
            "open_issues": d.get("open_issues_count", 0),
            "language": d.get("language") or "",
            "description": d.get("description") or "",
            "topics": d.get("topics", []) or [],
            "last_commit_days": last_commit_days,
            "updated_at": pushed_at,
        }
    except Exception as e:
        print(f"<!-- api meta error for {full_name}: {e} -->", file=sys.stderr)
        return {}


def momentum_score(repo: dict) -> tuple[float, dict]:
    """算动量分。返回 (final_score, debug_info)."""
    weekly = repo.get("weekly_stars", 0) or 0
    daily = repo.get("daily_stars", 0) or 0
    total = repo.get("stars", 0) or 0
    last_days = repo.get("last_commit_days")
    desc = repo.get("description", "") or ""

    # 1. 增长动量（占大头 0-100）
    if total > 0:
        growth_pct = (weekly / total) * 100
    else:
        growth_pct = 0
    momentum = min(70, growth_pct) + min(30, daily * 3)

    # 2. 活跃度加成（0/10/20）
    if last_days is None:
        active_bonus = 0
    elif last_days < 30:
        active_bonus = 20
    elif last_days < 90:
        active_bonus = 10
    elif last_days < 180:
        active_bonus = 0
    else:
        active_bonus = -20  # 半年没动，扣分

    # 3. 描述质量加成（0-15）
    desc_bonus = min(15, len(desc) / 8)

    final = max(0, momentum + active_bonus + desc_bonus)
    debug = {
        "growth_pct": round(growth_pct, 1),
        "momentum": round(momentum, 1),
        "active_bonus": active_bonus,
        "desc_bonus": round(desc_bonus, 1),
        "last_commit_days": last_days,
    }
    return final, debug


def main() -> int:
    print(f"<!-- GitHub Trending v2: top {LIMIT}, languages={LANGUAGES}, since={SINCE_OPTIONS} -->\n")

    # Phase 1: 抓 trending 列表（同时拿 daily + weekly 数据）
    raw = {}  # name -> {daily_stars, weekly_stars, ...}
    for lang in [""] + LANGUAGES:
        for since in SINCE_OPTIONS:
            for r in fetch_trending(lang, since):
                name = r["name"]
                if name not in raw:
                    raw[name] = {
                        "name": name,
                        "url": r["url"],
                        "description": r["description"],
                        "language": r.get("language") or lang,
                        "forks_trending": r.get("forks", 0),
                    }
                key = f"{since}_stars"
                raw[name][key] = r["stars"]

    # Phase 2: 每个 repo 调 REST API 拿 last commit / open issues / 真 stars
    metas = {}
    for name in list(raw.keys())[:LIMIT * 3]:  # 多抓点 API 数据
        meta = fetch_repo_meta(name)
        if meta:
            metas[name] = meta

    # Phase 3: 合并 + 评分
    enriched = []
    for name, r in raw.items():
        meta = metas.get(name, {})
        merged = {
            "name": name,
            "url": r["url"],
            "description": r.get("description") or meta.get("description", ""),
            "stars": meta.get("stars", 0),  # 用 API 真值，不用 trending 页面估值
            "forks": meta.get("forks", r.get("forks_trending", 0)),
            "open_issues": meta.get("open_issues", 0),
            "language": meta.get("language") or r.get("language", ""),
            "topics": meta.get("topics", []),
            "last_commit_days": meta.get("last_commit_days"),
            "daily_stars": r.get("daily_stars", 0),
            "weekly_stars": r.get("weekly_stars", 0),
        }
        score, debug = momentum_score(merged)
        merged["_score"] = score
        merged["_debug"] = debug
        enriched.append(merged)

    # 排序 + 截取
    enriched.sort(key=lambda x: x["_score"], reverse=True)
    enriched = enriched[:LIMIT]

    # 输出 Markdown
    print("# GitHub Trending — AI / Automation / Agent (按动量分排序)\n")
    print(f"> 综合信号：weekly 增速 + daily 增量 + 最近活跃度 + 描述质量")
    print(f"> 筛选维度不只看总 star，star 快速增长的项目优先\n")
    for r in enriched:
        score = r["_score"]
        d = r["_debug"]
        active = (
            f"⚡{d['last_commit_days']}d" if d["last_commit_days"] is not None and d["last_commit_days"] < 30
            else f"🕐{d['last_commit_days']}d" if d["last_commit_days"] is not None
            else "❓"
        )
        print(
            f"- **{r['name']}** | {r['url']} | "
            f"{r['description'][:100]} | "
            f"⭐ {r['stars']:,} 🔺 +{r['weekly_stars']}/w +{r['daily_stars']}/d | "
            f"🍴 {r['forks']:,} 🐛 {r['open_issues']} {active} | "
            f"📊 动量分 {score:.0f}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
