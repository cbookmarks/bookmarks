"""Shared helpers for reading and writing the resource data files.

Every script writes YAML through dump_resources() so files always have the
same layout. That keeps pull request diffs small and easy to review.
"""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RESOURCES = DATA / "resources"

# Field order in every entry. validate.py rejects unknown fields.
FIELDS = [
    "name",
    "url",
    "subcategory",
    "description",
    "keywords",
    "platforms",
    "works_with",
    "cost",
    "tags",
    "added",
    "submitted_by",
    "archived",
]


class _Dumper(yaml.SafeDumper):
    pass


def _str(dumper, value):
    return dumper.represent_scalar("tag:yaml.org,2002:str", value)


def _list(dumper, value):
    # Short lists of plain words read best inline: platforms: [macOS, iOS]
    flow = all(isinstance(v, str) and re.fullmatch(r"[\w.\-/ ]+", v) for v in value)
    return dumper.represent_sequence("tag:yaml.org,2002:seq", value, flow_style=flow)


_Dumper.add_representer(str, _str)
_Dumper.add_representer(list, _list)


def sort_key(entry: dict) -> str:
    name = entry.get("name", "").lower()
    return re.sub(r"^the\s+", "", name)


def ordered(entry: dict) -> dict:
    out = {k: entry[k] for k in FIELDS if k in entry and entry[k] not in (None, "", [])}
    out.update({k: v for k, v in entry.items() if k not in FIELDS})
    return out


def dump_resources(entries: list[dict]) -> str:
    entries = sorted((ordered(e) for e in entries), key=sort_key)
    chunks = [
        yaml.dump([e], Dumper=_Dumper, sort_keys=False, allow_unicode=True, width=1000)
        for e in entries
    ]
    return "\n".join(chunks)


def load_yaml(path: Path):
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_categories() -> list[dict]:
    return load_yaml(DATA / "categories.yaml")


def normalize_url(url: str) -> str:
    p = urlparse(url.strip())
    host = p.netloc.lower().removeprefix("www.")
    path = p.path.rstrip("/").lower()
    return host + path + (f"?{p.query}" if p.query else "")
