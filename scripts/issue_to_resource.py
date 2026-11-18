#!/usr/bin/env python3
"""Turn an approved submission issue into an entry in data/resources/<category>.yaml.

Run by .github/workflows/submission.yml. Reads the issue from environment variables:
ISSUE_BODY, ISSUE_USER. Writes the category id to $GITHUB_OUTPUT so the workflow
can name the pull request.
"""
from __future__ import annotations

import os
import re
import sys
from datetime import date

from resources_io import RESOURCES, dump_resources, load_categories, load_yaml, normalize_url
from validate import DESCRIPTION_MAX

EMPTY = {"", "_No response_", "None"}

# Checkbox labels in .github/ISSUE_TEMPLATE/resource-submission.yml -> ids in the data.
WORKS_WITH = {
    "Any MDM": "any-mdm",
    "Jamf": "jamf",
    "Microsoft Intune": "intune",
    "Iru (formerly Kandji)": "iru",
    "Mosyle": "mosyle",
    "Addigy": "addigy",
    "Munki": "munki",
}


def parse_issue_form(body: str) -> dict[str, str]:
    """GitHub issue forms render as '### Label' followed by the answer."""
    fields: dict[str, str] = {}
    for block in re.split(r"^### ", body, flags=re.M)[1:]:
        label, _, value = block.partition("\n")
        fields[label.strip()] = value.strip()
    return fields


def checked(value: str) -> list[str]:
    return [m.strip() for m in re.findall(r"- \[[xX]\] (.+)", value)]


def main() -> int:
    form = parse_issue_form(os.environ["ISSUE_BODY"])
    get = lambda label: "" if form.get(label, "") in EMPTY else form.get(label, "")

    categories = {c["name"]: c for c in load_categories()}
    category = categories.get(get("Category"))
    if not category:
        print(f"Unknown category: {get('Category')!r}")
        return 1

    entry = {
        "name": get("Name"),
        "url": get("URL"),
        "subcategory": get("Subcategory"),
        "description": " ".join(get("Description").split()),
        "keywords": [k.strip().lower() for k in get("Keywords").split(",") if k.strip()][:8],
        "platforms": checked(form.get("Platforms", "")),
        "works_with": [WORKS_WITH[w] for w in checked(form.get("Works with", "")) if w in WORKS_WITH],
        "cost": get("Cost"),
        "added": date.today(),
    }
    if len(entry["description"]) > DESCRIPTION_MAX:
        # GitHub forms can't limit length. Leave it out and show the original in the pull request,
        # so the maintainer can shorten it before merging.
        print(f"Description was {len(entry['description'])} characters, over the {DESCRIPTION_MAX} limit; "
              f"shorten it and add it before merging. Original: {entry['description']}")
        entry["description"] = ""

    user = os.environ.get("ISSUE_USER")
    if user:
        entry["submitted_by"] = f"@{user}"

    existing = {}
    for path in RESOURCES.glob("*.yaml"):
        for e in load_yaml(path) or []:
            existing[normalize_url(e["url"])] = f"{e['name']} in {path.name}"
    if normalize_url(entry["url"]) in existing:
        print(f"Already listed: {existing[normalize_url(entry['url'])]}")
        return 1

    path = RESOURCES / f"{category['id']}.yaml"
    entries = load_yaml(path) or []
    entries.append(entry)
    path.write_text(dump_resources(entries), encoding="utf-8")
    print(f"Added {entry['name']} to {path.name}")

    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as fh:
            fh.write(f"category={category['id']}\nname={entry['name']}\nurl={entry['url']}\nfile=data/resources/{category['id']}.yaml\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
