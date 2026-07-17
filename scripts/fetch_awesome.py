#!/usr/bin/env python3
"""fetch_awesome.py — 监控 awesome-* AI/Agent 列表的更新"""

import sys
import requests
from datetime import datetime

# 关注的 awesome 列表
REPOS = [
    "awesome-chatgpt-prompts/awesome-chatgpt-prompts",
    "f/awesome-chatgpt-prompts",
    "milvus-io/awesome-milvus",
    "e2b-dev/awesome-ai-agents",
    "kaushikbhadra/Awesome-Cursor-MCP-Server",
    "MCP-Mirror/mcp_mirror",
    "jlowin/fastmcp",
    "anthropics/anthropic-cookbook",
    "openai/openai-cookbook",
]


def fetch_recent_commits(repo: str) -> list[dict]:
    """Fetch recent commits for an awesome-* repo."""
    url = f"https://api.github.com/repos/{repo}/commits?per_page=3"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "JingTai-Curator/1.0",
    }
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200:
            return []
        out = []
        for c in r.json()[:3]:
            msg = c.get("commit", {}).get("message", "").split("\n")[0][:120]
            sha = c.get("sha", "")[:7]
            date = c.get("commit", {}).get("author", {}).get("date", "")
            out.append({"sha": sha, "msg": msg, "date": date})
        return out
    except Exception as e:
        print(f"<!-- awesome fetch error {repo}: {e} -->", file=sys.stderr)
        return []


def main() -> int:
    print(f"<!-- awesome-* updates: {len(REPOS)} repos -->\n")
    print(f"<!-- Checked at {datetime.utcnow().isoformat()}Z -->\n")
    print("# awesome-* 列表 — 最近更新\n")
    for repo in REPOS:
        commits = fetch_recent_commits(repo)
        if not commits:
            continue
        print(f"\n## {repo}\n")
        for c in commits:
            print(f"- **{c['sha']}** | {c['date'][:10]} | {c['msg']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
