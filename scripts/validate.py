#!/usr/bin/env python3
"""Check every file in data/resources/ against the rules in CONTRIBUTING.md.

    python scripts/validate.py         # report problems, exit 1 if any
    python scripts/validate.py --fix   # also rewrite files in the standard layout and order
"""
from __future__ import annotations

import re
import sys
from datetime import date

from resources_io import FIELDS, RESOURCES, dump_resources, load_categories, load_yaml, normalize_url

PLATFORMS = {"macOS", "iOS", "iPadOS", "tvOS", "visionOS", "watchOS"}
WORKS_WITH = {"any-mdm", "jamf", "intune", "iru", "mosyle", "addigy", "filewave", "workspace-one", "hexnode", "simplemdm", "jumpcloud", "fleet", "munki"}
COSTS = {"free", "open-source", "paid", "freemium"}
TAGS = {"rss", "http-only", "apple"}
URL_RE = re.compile(r"^https?://[^\s/$.?#][^\s]*\.[^\s]+$")
TRACKING_RE = re.compile(r"[?&](ref|aff|affiliate|utm_[a-z]+)=", re.I)
DESCRIPTION_MAX = 140
KEYWORDS_MAX = 8


def main() -> int:
    fix = "--fix" in sys.argv
    errors: list[str] = []
    categories = {c["id"]: c for c in load_categories()}
    seen: dict[str, str] = {}

    files = sorted(RESOURCES.glob("*.yaml"))
    for path in files:
        cat_id = path.stem
        where = f"data/resources/{path.name}"
        if cat_id not in categories:
            errors.append(f"{where}: no category with id '{cat_id}' in data/categories.yaml")
            continue
        subs = set(categories[cat_id].get("subcategories") or [])
        entries = load_yaml(path) or []
        if not isinstance(entries, list):
            errors.append(f"{where}: must be a list of resources")
            continue

        for n, e in enumerate(entries, 1):
            label = f"{where} #{n} ({e.get('name', '?')})" if isinstance(e, dict) else f"{where} #{n}"
            if not isinstance(e, dict):
                errors.append(f"{label}: each resource must be a set of fields")
                continue
            for key in e:
                if key not in FIELDS:
                    errors.append(f"{label}: unknown field '{key}'")
            for key in ("name", "url"):
                if not str(e.get(key) or "").strip():
                    errors.append(f"{label}: '{key}' is required")
            url = str(e.get("url") or "")
            if url and not URL_RE.match(url):
                errors.append(f"{label}: url must be a full http(s) address")
            if url.startswith("http://") and "http-only" not in (e.get("tags") or []):
                errors.append(f"{label}: use https://, or add the tag http-only if the site has no https")
            if TRACKING_RE.search(url):
                errors.append(f"{label}: remove referral or tracking parameters from the url")
            if url:
                key = normalize_url(url)
                if key in seen:
                    errors.append(f"{label}: duplicate of {seen[key]}")
                else:
                    seen[key] = label
            sub = e.get("subcategory")
            if sub and sub not in subs:
                errors.append(f"{label}: subcategory '{sub}' is not listed for '{cat_id}' in data/categories.yaml")
            desc = e.get("description")
            if desc and len(desc) > DESCRIPTION_MAX:
                errors.append(f"{label}: description is {len(desc)} characters, keep it to {DESCRIPTION_MAX}")
            kws = e.get("keywords")
            if kws is not None:
                if not isinstance(kws, list) or not all(isinstance(k, str) for k in kws):
                    errors.append(f"{label}: keywords must be a list of words, like [filevault, escrow]")
                else:
                    if len(kws) > KEYWORDS_MAX:
                        errors.append(f"{label}: {len(kws)} keywords, keep it to {KEYWORDS_MAX}")
                    for k in kws:
                        if k != k.lower() or not k.strip() or len(k) > 40:
                            errors.append(f"{label}: keyword '{k}' must be lowercase and at most 40 characters")
            for key, allowed in (("platforms", PLATFORMS), ("works_with", WORKS_WITH), ("tags", TAGS)):
                for v in e.get(key) or []:
                    if v not in allowed:
                        errors.append(f"{label}: '{v}' is not an allowed value for {key} ({', '.join(sorted(allowed))})")
            if e.get("cost") and e["cost"] not in COSTS:
                errors.append(f"{label}: cost must be one of {', '.join(sorted(COSTS))}")
            if e.get("added") and not isinstance(e["added"], date):
                errors.append(f"{label}: added must be a date like 2026-10-24")
            if e.get("archived") not in (None, True, False):
                errors.append(f"{label}: archived must be true or false")

        canonical = dump_resources(entries)
        if path.read_text(encoding="utf-8") != canonical:
            if fix:
                path.write_text(canonical, encoding="utf-8")
                print(f"Reformatted {where}")
            else:
                errors.append(f"{where}: not in the standard order or layout. Run: python scripts/validate.py --fix")

    for cat_id in categories:
        if not (RESOURCES / f"{cat_id}.yaml").exists():
            errors.append(f"data/categories.yaml: category '{cat_id}' has no file data/resources/{cat_id}.yaml")

    # The submission form's category dropdown must match data/categories.yaml.
    form = RESOURCES.parent.parent / ".github" / "ISSUE_TEMPLATE" / "resource-submission.yml"
    if form.exists():
        fields = {f.get("id"): f for f in load_yaml(form)["body"]}
        options = fields.get("category", {}).get("attributes", {}).get("options", [])
        names = [c["name"] for c in categories.values()]
        if options != names:
            errors.append(f"{form.relative_to(RESOURCES.parent.parent)}: category options must match the names in data/categories.yaml, in order: {', '.join(names)}")

    if errors:
        print(f"Found {len(errors)} problem(s):")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"OK: {len(seen)} resources in {len(files)} files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
