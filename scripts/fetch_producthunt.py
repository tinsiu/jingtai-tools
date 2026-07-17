#!/usr/bin/env python3
"""fetch_producthunt.py — 抓 Product Hunt AI 类别 Top"""

import os
import sys
import requests

LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 15
TOKEN = os.environ.get("PH_TOKEN", "")


def fetch_via_api() -> list[dict]:
    """Try Product Hunt public API."""
    if not TOKEN:
        return []
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/json",
    }
    query = """
    query {
      posts(first: %d, order: VOTES, topic: "ai") {
        edges {
          node {
            name
            tagline
            url
            votesCount
          }
        }
      }
    }
    """ % LIMIT
    try:
        r = requests.post(
            "https://api.producthunt.com/v2/api/graphql",
            json={"query": query},
            headers=headers,
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        edges = data.get("data", {}).get("posts", {}).get("edges", [])
        return [
            {
                "name": e["node"]["name"],
                "tagline": e["node"]["tagline"],
                "url": e["node"]["url"],
                "votes": e["node"]["votesCount"],
            }
            for e in edges
        ]
    except Exception as e:
        print(f"<!-- PH API error: {e} -->", file=sys.stderr)
        return []


def fetch_via_html() -> list[dict]:
    """Fallback: scrape PH HTML."""
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        r = requests.get("https://www.producthunt.com/topics/artificial-intelligence",
                         headers=headers, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"<!-- PH HTML error: {e} -->", file=sys.stderr)
        return []

    # Heuristic parser
    import re
    out = []
    for m in re.finditer(r'data-test="post-name"[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>.*?data-test="post-tagline"[^>]*>([^<]+)</a>', r.text, re.DOTALL):
        url, name, tagline = m.group(1), m.group(2).strip(), m.group(3).strip()
        if not url.startswith("http"):
            url = "https://www.producthunt.com" + url
        out.append({"name": name, "tagline": tagline, "url": url, "votes": 0})
    return out[:LIMIT]


def main() -> int:
    print(f"<!-- Product Hunt AI: top {LIMIT} -->\n")
    items = fetch_via_api()
    if not items:
        items = fetch_via_html()
    print("# Product Hunt — AI 类别\n")
    for r in items:
        print(f"- **{r['name']}** | {r['url']} | {r['tagline'][:120]} | 🔺 {r['votes']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
