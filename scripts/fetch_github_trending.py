#!/usr/bin/env python3
"""fetch_github_trending.py — 抓 GitHub Trending AI/Automation/Agent"""

import sys
import requests
from bs4 import BeautifulSoup

LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 20
LANGUAGES = ["python", "typescript", "javascript", "rust", "go"]

def fetch_trending(language: str = "") -> list[dict]:
    """Fetch trending repos, optionally filtered by language."""
    url = f"https://github.com/trending/{language}" if language else "https://github.com/trending"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        r = requests.get(url, headers=headers, timeout=15)
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
            stars_el = article.select_one("a[href$='/stargazers']")
            stars = 0
            if stars_el:
                txt = stars_el.get_text(strip=True).replace(",", "")
                try:
                    stars = int(float(txt.split()[0]) * (1000 if "k" in txt.lower() else 1))
                except Exception:
                    pass
            lang_el = article.select_one("[itemprop='programmingLanguage']")
            lang = lang_el.get_text(strip=True) if lang_el else ""
            repos.append({
                "name": full_name,
                "url": f"https://github.com/{full_name}",
                "description": desc,
                "stars": stars,
                "language": lang or language,
            })
        except Exception as e:
            print(f"<!-- parse error: {e} -->", file=sys.stderr)
            continue
    return repos


def main() -> int:
    print(f"<!-- GitHub Trending: top {LIMIT} per language, languages={LANGUAGES} -->\n")
    seen = set()
    out = []
    for lang in [""] + LANGUAGES:
        for r in fetch_trending(lang):
            if r["name"] in seen:
                continue
            seen.add(r["name"])
            out.append(r)
            if len(out) >= LIMIT:
                break
        if len(out) >= LIMIT:
            break

    print("# GitHub Trending — AI / Automation / Agent\n")
    for r in out:
        print(f"- **{r['name']}** | {r['url']} | {r['description'][:120]} | ⭐ {r['stars']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
