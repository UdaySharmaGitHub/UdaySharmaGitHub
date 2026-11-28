#!/usr/bin/env python3
"""
Fetch the 3 most recently pushed-to repos for UdaySharmaGitHub and write
data/repos.json. Run daily by update-profile-art.yml before
render_readme_cards.py so the repo cards always show current work.

No auth required for public repos; set GITHUB_TOKEN env var to raise the
rate limit from 60 to 5000 requests/hour (useful in GitHub Actions).
"""
import json
import os
import sys

import requests

USERNAME = os.environ.get("GH_PROFILE_USER", "UdaySharmaGitHub")
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "repos.json")
COUNT = 3  # number of repo cards shown in the README

# GitHub language name → Three Worlds card accent colour
LANG_COLOR = {
    "TypeScript":       "#2f55ff",   # TECH blue
    "JavaScript":       "#ffc81a",   # LEARN yellow
    "Python":           "#2f55ff",   # TECH blue
    "Jupyter Notebook": "#ffc81a",   # LEARN yellow
    "C++":              "#ef3b2d",   # STUDIO red
    "C":                "#ef3b2d",
    "C#":               "#ef3b2d",
    "Java":             "#ef3b2d",
    "Kotlin":           "#ef3b2d",
    "Rust":             "#ef3b2d",
    "Go":               "#2f55ff",
    "Shell":            "#2f55ff",
    "HTML":             "#ffc81a",
    "CSS":              "#2f55ff",
    "SCSS":             "#2f55ff",
    "Swift":            "#ef3b2d",
    "Dart":             "#2f55ff",
}
DEFAULT_COLOR = "#6e6e73"  # muted gray fallback

DISPLAY_MAX = 14  # max chars for the short label shown as the card title


def short_name(name):
    """Derive a short display label from a repo name."""
    for strip in ["-main", "-master", "-repo", "-project"]:
        if name.lower().endswith(strip):
            name = name[: -len(strip)]
    return name[:DISPLAY_MAX]


def fetch_repos():
    url = (
        f"https://api.github.com/users/{USERNAME}/repos"
        f"?sort=pushed&per_page=50&type=owner"
    )
    headers = {
        "User-Agent": "profile-readme-bot/1.0",
        "Accept": "application/vnd.github+json",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    all_repos = resp.json()

    # Keep only own (non-fork), non-archived repos
    repos = [
        r for r in all_repos
        if not r.get("fork") and not r.get("archived") and r.get("name")
    ]

    top = repos[:COUNT]
    result = []
    for r in top:
        lang = r.get("language") or "Code"
        desc = (r.get("description") or r["name"])
        if len(desc) > 80:
            desc = desc[:77] + "..."
        result.append({
            "name":        r["name"],
            "display":     short_name(r["name"]),
            "description": desc,
            "language":    lang,
            "color":       LANG_COLOR.get(lang, DEFAULT_COLOR),
            "stars":       r.get("stargazers_count", 0),
        })

    return result


if __name__ == "__main__":
    try:
        repos = fetch_repos()
    except Exception as e:
        print(f"fetch_repos failed: {e} — keeping existing data/repos.json", file=sys.stderr)
        sys.exit(0)   # non-fatal: keep last good repos.json, continue the pipeline

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(repos, f, indent=2)
    print(f"wrote {OUT_PATH}: {[r['name'] for r in repos]}")
