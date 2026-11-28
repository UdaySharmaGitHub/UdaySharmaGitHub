#!/usr/bin/env python3
"""
Fetch headline profile stats for UdaySharmaGitHub and write data/stats.json.
Run daily by update-profile-art.yml before render_readme_cards.py so the
stat tiles (followers, stars, repos, tutorials) always show current numbers.

Uses only the free, unauthenticated GitHub REST API (public data). Set
GITHUB_TOKEN to raise the rate limit from 60 to 5000 requests/hour (CI).
"""
import json
import os
import sys

import requests

USERNAME = os.environ.get("GH_PROFILE_USER", "UdaySharmaGitHub")
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "stats.json")

# A repo counts as "learning" content if any of these appears in its name or
# description (case-insensitive). Keeps the TUTORIALS tile honest + automatic.
LEARN_KEYWORDS = [
    "tutorial", "guide", "complete", "mastery", "zero-to-hero", "quick-start",
    "quick start", "learn", "pattern", "challenge", "problem", "technique",
    "bootcamp", "course", "example", "hands-on", "notes",
]


def headers():
    h = {
        "User-Agent": "profile-readme-bot/1.0",
        "Accept": "application/vnd.github+json",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def is_learning(repo):
    hay = (repo.get("name", "") + " " + (repo.get("description") or "")).lower()
    return any(k in hay for k in LEARN_KEYWORDS)


def fetch_stats():
    user = requests.get(
        f"https://api.github.com/users/{USERNAME}", headers=headers(), timeout=30
    )
    user.raise_for_status()
    u = user.json()

    repos = []
    for page in range(1, 6):  # up to 500 repos
        resp = requests.get(
            f"https://api.github.com/users/{USERNAME}/repos"
            f"?per_page=100&type=owner&page={page}",
            headers=headers(), timeout=30,
        )
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        repos.extend(batch)

    owned = [r for r in repos if not r.get("fork") and not r.get("archived")]
    stars = sum(r.get("stargazers_count", 0) for r in owned)
    forks = sum(r.get("forks_count", 0) for r in owned)
    tutorials = sum(1 for r in owned if is_learning(r))

    return {
        "followers":   u.get("followers", 0),
        "repos_owned": len(owned),
        "public_repos": u.get("public_repos", 0),
        "stars":       stars,
        "forks":       forks,
        "tutorials":   tutorials,
    }


if __name__ == "__main__":
    try:
        stats = fetch_stats()
    except Exception as e:
        print(f"fetch_stats failed: {e} — keeping existing data/stats.json", file=sys.stderr)
        sys.exit(0)  # non-fatal: keep last good stats.json, continue the pipeline

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"wrote {OUT_PATH}: {stats}")
