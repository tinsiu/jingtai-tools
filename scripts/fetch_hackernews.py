#!/usr/bin/env python3
"""fetch_hackernews.py — 抓 HN Show HN + AI 标签"""

import sys
import requests

LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 15
TAGS = ["AI", "show_hn"]


def fetch_hn(tag: str) -> list[dict]:
    url = f"https://hacker-news.firebaseio.com/v0/{tag}stories.json"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        ids = r.json() or []
    except Exception as e:
        print(f"<!-- HN fetch error {tag}: {e} -->", file=sys.stderr)
        return []

    items = []
    for sid in ids[: LIMIT * 2]:
        try:
            r = requests.get(
                f"https://hacker-news.firebaseio.com/v0/item/{sid}.json",
                timeout=10,
            )
            r.raise_for_status()
            d = r.json()
            if not d:
                continue
            title = d.get("title") or ""
            url_item = d.get("url") or f"https://news.ycombinator.com/item?id={sid}"
            score = d.get("score", 0)
            desc = d.get("text", "")[:200] if d.get("text") else ""
            items.append({
                "title": title,
                "url": url_item,
                "score": score,
                "desc": desc,
                "tag": tag,
            })
            if len(items) >= LIMIT:
                break
        except Exception as e:
            print(f"<!-- HN item error {sid}: {e} -->", file=sys.stderr)
            continue
    return items


def main() -> int:
    print(f"<!-- Hacker News: top {LIMIT} per tag, tags={TAGS} -->\n")
    seen = set()
    out = []
    for tag in TAGS:
        for r in fetch_hn(tag):
            key = r["url"]
            if key in seen:
                continue
            seen.add(key)
            out.append(r)
            if len(out) >= LIMIT:
                break
        if len(out) >= LIMIT:
            break

    print("# Hacker News — AI + Show HN\n")
    for r in out:
        print(f"- **{r['title']}** | {r['url']} | {r['desc']} | ▲ {r['score']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
