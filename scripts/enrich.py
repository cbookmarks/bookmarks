#!/usr/bin/env python3
"""Fill in missing details for a resource: description, keywords, platforms, cost.

Sources:
  - GitHub API, for github.com repositories: About text, topics, licence, archived.
    These are filled in automatically.
  - Other sites: the site's own description is shown in the report as a suggestion,
    not filled in, because it is often marketing copy.

Only empty fields are filled; anything a submitter or maintainer wrote is kept.

    # Fill one entry in a data file (used by .github/workflows/submission.yml)
    python scripts/enrich.py --file data/resources/tools.yaml --url https://github.com/org/tool

    # Try it on some URLs without changing anything
    python scripts/enrich.py --dry-run https://example.com https://github.com/org/tool

Environment: GITHUB_TOKEN (optional, raises the GitHub API rate limit).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

from resources_io import dump_resources, load_yaml, normalize_url
from validate import COSTS, DESCRIPTION_MAX, KEYWORDS_MAX, PLATFORMS, WORKS_WITH

USER_AGENT = "CommunityBookmarks/1.0 (+https://github.com/cbookmarks/bookmarks)"
GENERIC = {"mac", "macos", "apple", "macadmin", "macadmins", "mac admin", "mac admins", "tool", "tools",
           "website", "admin", "sysadmin", "it", "osx", "macosx", "swift", "bash", "zsh", "python", "shell"}
OPEN_LICENCES = {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "GPL-2.0", "GPL-3.0", "LGPL-2.1",
                 "LGPL-3.0", "MPL-2.0", "ISC", "Unlicense", "AGPL-3.0", "0BSD", "CC0-1.0", "EPL-2.0"}


class _Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title, self.meta, self._in_title = "", {}, False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title":
            self._in_title = True
        elif tag == "meta":
            key = (a.get("name") or a.get("property") or "").lower()
            if key in ("description", "og:description", "og:title", "twitter:description") and a.get("content"):
                self.meta[key] = a["content"].strip()

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def http(url: str, headers: dict | None = None, timeout: int = 25) -> tuple[int, bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read(2_000_000)
    except urllib.error.HTTPError as e:
        try:
            return e.code, e.read(4000)
        except Exception:
            return e.code, b""
    except Exception:
        return 0, b""


def github_info(url: str, token: str | None) -> dict | None:
    m = re.match(r"https?://(?:www\.)?github\.com/([^/]+)/([^/#?]+)", url)
    if not m or m.group(1) in ("orgs", "apps", "sponsors"):
        return None
    owner, repo = m.group(1), m.group(2).removesuffix(".git")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    status, body = http(f"https://api.github.com/repos/{owner}/{repo}", headers)
    if status != 200:
        return None
    info = json.loads(body)
    return {
        "about": (info.get("description") or "").strip(),
        "topics": info.get("topics") or [],
        "licence": (info.get("license") or {}).get("spdx_id"),
        "archived": bool(info.get("archived")),
    }


def page_info(url: str) -> dict:
    status, body = http(url, {"Accept": "text/html,application/xhtml+xml"})
    if status != 200 or not body:
        return {"status": status}
    p = _Text()
    try:
        p.feed(body.decode("utf-8", "replace"))
    except Exception:
        pass
    return {
        "status": status,
        "title": " ".join(p.title.split()),
        "site_description": p.meta.get("description") or p.meta.get("og:description") or p.meta.get("twitter:description", ""),
    }


def clean(result: dict) -> dict:
    """Keep only values that pass the same rules as validate.py."""
    out = {}
    desc = " ".join(str(result.get("description") or "").split())
    if 0 < len(desc) <= DESCRIPTION_MAX:
        out["description"] = desc
    kws = [str(k).strip().lower() for k in result.get("keywords") or [] if str(k).strip()]
    kws = [k for k in dict.fromkeys(kws) if len(k) <= 40 and k not in GENERIC][:min(6, KEYWORDS_MAX)]
    if kws:
        out["keywords"] = kws
    for key, allowed in (("platforms", PLATFORMS), ("works_with", WORKS_WITH)):
        vals = [v for v in result.get(key) or [] if v in allowed]
        if vals:
            out[key] = vals
    if result.get("cost") in COSTS:
        out["cost"] = result["cost"]
    return out


def enrich(entry: dict, token: str | None) -> tuple[dict, list[str]]:
    """Return (fields to fill, report lines). Never overwrites fields that already have a value."""
    found: dict = {}
    report: list[str] = []
    gh = github_info(entry["url"], token)
    if gh:
        if gh["about"] and len(gh["about"]) <= DESCRIPTION_MAX:
            found["description"] = gh["about"].rstrip() if gh["about"].endswith(".") else gh["about"].rstrip() + "."
        topics = [t.replace("-", " ") for t in gh["topics"]]
        if topics:
            found["keywords"] = topics
        if gh["licence"] in OPEN_LICENCES:
            found["cost"] = "open-source"
        if gh["archived"]:
            found["archived"] = True
            report.append("the GitHub repository is archived")
        source = "GitHub"
    else:
        source = "the page"
        page = page_info(entry["url"])
        if page["status"] != 200:
            report.append(f"page could not be read (HTTP {page['status'] or 'error'}); check the link")
        elif page.get("site_description"):
            report.append(f"the site describes itself as: \"{' '.join(page['site_description'].split())[:300]}\"")

    fill = {k: v for k, v in clean(found).items() if not entry.get(k)}
    if found.get("archived") and not entry.get("archived"):
        fill["archived"] = True
    report.insert(0, f"filled {', '.join(fill)} from {source}" if fill else "nothing filled in automatically")
    if not entry.get("description") and "description" not in fill:
        report.append("no description yet: add one before merging")
    return fill, report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", type=Path, help="data file that contains the entry")
    ap.add_argument("--url", help="url of the entry to fill in")
    ap.add_argument("--dry-run", nargs="+", metavar="URL", help="show what would be filled for these URLs")
    args = ap.parse_args()
    token = os.environ.get("GITHUB_TOKEN")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")

    if args.dry_run:
        lines = ["## Fill-in preview", ""]
        for url in args.dry_run:
            fill, report = enrich({"url": url, "name": ""}, token)
            lines += [f"### {url}", "", "```yaml", dump_resources([{"name": "(name)", "url": url, **fill}]).strip(),
                      "```", "", *[f"- {r}" for r in report], ""]
        out = "\n".join(lines)
        print(out)
        if summary:
            Path(summary).write_text(out, encoding="utf-8")
        return 0

    if not (args.file and args.url):
        ap.error("use --file and --url, or --dry-run")
    entries = load_yaml(args.file) or []
    target = next((e for e in entries if normalize_url(e["url"]) == normalize_url(args.url)), None)
    if not target:
        print(f"No entry with url {args.url} in {args.file}", file=sys.stderr)
        return 1
    fill, report = enrich(target, token)
    target.update(fill)
    args.file.write_text(dump_resources(entries), encoding="utf-8")
    print("\n".join(f"- {r}" for r in report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
