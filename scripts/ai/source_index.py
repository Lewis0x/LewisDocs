# Copyright 2026

"""Generate the complete AI source manifest from committed official indexes."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal, TypedDict, cast
from urllib.parse import urlparse

import httpx2

Product = Literal["claude-code", "codex"]

_ROOT: Final = Path(__file__).resolve().parents[2]
_SOURCE_ROOT: Final = _ROOT / "source-ai"
_MANIFEST_PATH: Final = _SOURCE_ROOT / "sources.yaml"
_INDEX_ROOT: Final = _SOURCE_ROOT / "indexes"
_INDEX_URLS: Final[dict[Product, str]] = {
    "claude-code": "https://code.claude.com/docs/llms.txt",
    "codex": "https://developers.openai.com/codex/llms.txt",
}
_INDEX_PATHS: Final[dict[Product, Path]] = {
    product: _INDEX_ROOT / f"{product}.txt" for product in _INDEX_URLS
}
_EXPECTED_COUNTS: Final[dict[Product, int]] = {"claude-code": 172, "codex": 131}
_ENTRY_RE: Final = re.compile(r"^- \[(?P<title>.+)]\((?P<url>https://[^)]+)\)(?:: .*)?$")
_HEADING_RE: Final = re.compile(r"^##\s+(?P<section>.+?)\s*$")

# These routes were published before the complete index was added. Keep them stable.
_LEGACY_OFFICIAL_URLS: Final[dict[str, str]] = {
    "claude-code/quickstart": "https://code.claude.com/docs/en/quickstart.md",
    "claude-code/memory": "https://code.claude.com/docs/en/memory.md",
    "claude-code/permissions": "https://code.claude.com/docs/en/permissions.md",
    "claude-code/extensions": "https://code.claude.com/docs/en/features-overview.md",
    "claude-code/best-practices": "https://code.claude.com/docs/en/best-practices.md",
    "claude-code/how-it-works": "https://code.claude.com/docs/en/how-claude-code-works.md",
    "claude-code/common-workflows": "https://code.claude.com/docs/en/common-workflows.md",
    "claude-code/hooks-guide": "https://code.claude.com/docs/en/hooks-guide.md",
    "claude-code/mcp": "https://code.claude.com/docs/en/mcp.md",
    "claude-code/subagents": "https://code.claude.com/docs/en/sub-agents.md",
    "codex/cli": "https://developers.openai.com/codex/cli.md",
    "codex/prompting": "https://developers.openai.com/codex/prompting.md",
    "codex/agents-md": "https://developers.openai.com/codex/agent-configuration/agents-md.md",
    "codex/approvals-security": (
        "https://developers.openai.com/codex/agent-approvals-security.md"
    ),
    "codex/customization": "https://developers.openai.com/codex/customization/overview.md",
    "codex/best-practices": "https://developers.openai.com/codex/learn/best-practices.md",
    "codex/ide": "https://developers.openai.com/codex/ide.md",
    "codex/cloud": "https://developers.openai.com/codex/cloud.md",
    "codex/mcp": "https://developers.openai.com/codex/extend/mcp.md",
    "codex/github-action": "https://developers.openai.com/codex/github-action.md",
}
_HTML_FETCH_OVERRIDES: Final[dict[str, str]] = {
    "https://developers.openai.com/codex/community/codex-for-oss.md": (
        "https://developers.openai.com/community/codex-for-oss"
    ),
    "https://developers.openai.com/codex/guides/build-ai-native-engineering-team.md": (
        "https://learn.chatgpt.com/guides/build-ai-native-engineering-team"
    ),
    "https://developers.openai.com/codex/overview.md": "https://learn.chatgpt.com/docs",
    "https://developers.openai.com/codex/resources.md": "https://learn.chatgpt.com/resources",
    "https://developers.openai.com/codex/videos.md": "https://learn.chatgpt.com/videos",
}
_ROUTE_SLUG_OVERRIDES: Final[dict[str, str]] = {
    "https://code.claude.com/docs/en/whats-new/index.md": "whats-new",
}


class ManifestRow(TypedDict):
    """Serialized source row."""

    id: str
    product: Product
    slug: str
    title: str
    section: str
    canonical_url: str
    fetch_url: str
    fetch_format: Literal["markdown", "html", "html-main"]
    owner: Literal["Anthropic", "OpenAI"]


@dataclass(frozen=True, slots=True)
class IndexEntry:
    """One link from an official compact index."""

    product: Product
    section: str
    title: str
    url: str


def parse_index(text: str, product: Product) -> tuple[IndexEntry, ...]:
    """Parse one official ``llms.txt`` into its individual page entries."""
    section = ""
    entries: list[IndexEntry] = []
    for raw_line in text.replace("\r\n", "\n").replace("\r", "\n").splitlines():
        if heading := _HEADING_RE.fullmatch(raw_line):
            section = heading["section"]
            continue
        match = _ENTRY_RE.fullmatch(raw_line)
        if match is None or (product == "codex" and section == "Documentation sets"):
            continue
        if not section:
            msg = "official index entry appears before a section heading"
            raise ValueError(msg)
        entries.append(
            IndexEntry(
                product=product,
                section=section,
                title=match["title"],
                url=match["url"],
            )
        )
    expected = _EXPECTED_COUNTS[product]
    if len(entries) != expected:
        msg = f"{product} index contains {len(entries)} entries; expected {expected}"
        raise ValueError(msg)
    if len({entry.url for entry in entries}) != len(entries):
        msg = f"{product} index contains duplicate URLs"
        raise ValueError(msg)
    return tuple(entries)


def generate_manifest(
    indexes: dict[Product, str],
    legacy_rows: tuple[ManifestRow, ...],
) -> tuple[ManifestRow, ...]:
    """Generate all rows while preserving the previously published core routes."""
    entries = tuple(
        entry
        for product in ("claude-code", "codex")
        for entry in parse_index(indexes[cast("Product", product)], cast("Product", product))
    )
    entry_by_url = {entry.url: entry for entry in entries}
    legacy_by_url: dict[str, ManifestRow] = {}
    legacy_order: dict[Product, list[str]] = {"claude-code": [], "codex": []}
    for row in legacy_rows:
        official_url = _LEGACY_OFFICIAL_URLS.get(row["id"])
        if official_url is None:
            continue
        legacy_by_url[official_url] = row
        legacy_order[row["product"]].append(official_url)
    if set(legacy_by_url) != set(_LEGACY_OFFICIAL_URLS.values()):
        msg = "legacy manifest rows required for stable routes are missing"
        raise ValueError(msg)
    if not set(legacy_by_url) <= set(entry_by_url):
        msg = "an official index no longer contains a stable legacy source"
        raise ValueError(msg)

    generated: list[ManifestRow] = []
    for product in ("claude-code", "codex"):
        typed_product = cast("Product", product)
        product_entries = [entry for entry in entries if entry.product == typed_product]
        ordered_urls = legacy_order[typed_product] + [
            entry.url for entry in product_entries if entry.url not in legacy_by_url
        ]
        for url in ordered_urls:
            entry = entry_by_url[url]
            if legacy := legacy_by_url.get(url):
                row = dict(legacy)
                row["section"] = entry.section
                generated.append(cast("ManifestRow", row))
            else:
                generated.append(_new_row(entry))
    if len(generated) != sum(_EXPECTED_COUNTS.values()):
        msg = "generated manifest has the wrong number of rows"
        raise ValueError(msg)
    if len({row["id"] for row in generated}) != len(generated):
        msg = "generated manifest contains duplicate routes"
        raise ValueError(msg)
    return tuple(generated)


def _new_row(entry: IndexEntry) -> ManifestRow:
    slug = _ROUTE_SLUG_OVERRIDES.get(entry.url, _slug_from_url(entry))
    fetch_url = _HTML_FETCH_OVERRIDES.get(entry.url, entry.url)
    return {
        "id": f"{entry.product}/{slug}",
        "product": entry.product,
        "slug": slug,
        "title": entry.title,
        "section": entry.section,
        "canonical_url": entry.url.removesuffix(".md"),
        "fetch_url": fetch_url,
        "fetch_format": (
            "html-main"
            if entry.url.endswith("/community/codex-for-oss.md")
            else "html"
            if entry.url in _HTML_FETCH_OVERRIDES
            else "markdown"
        ),
        "owner": "Anthropic" if entry.product == "claude-code" else "OpenAI",
    }


def _slug_from_url(entry: IndexEntry) -> str:
    path = urlparse(entry.url).path
    prefix = "/docs/en/" if entry.product == "claude-code" else "/codex/"
    if not path.startswith(prefix) or not path.endswith(".md"):
        msg = f"unexpected official source URL: {entry.url}"
        raise ValueError(msg)
    return path.removeprefix(prefix).removesuffix(".md")


def _load_legacy_rows() -> tuple[ManifestRow, ...]:
    payload = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        msg = "source manifest must contain a JSON list"
        raise TypeError(msg)
    return tuple(cast("ManifestRow", row) for row in payload)


def _read_indexes() -> dict[Product, str]:
    return {product: path.read_text(encoding="utf-8") for product, path in _INDEX_PATHS.items()}


def _refresh_indexes() -> None:
    _INDEX_ROOT.mkdir(parents=True, exist_ok=True)
    with httpx2.Client(follow_redirects=True, timeout=60.0) as client:
        for product, url in _INDEX_URLS.items():
            response = client.get(url)
            response.raise_for_status()
            _INDEX_PATHS[product].write_text(response.text, encoding="utf-8", newline="\n")


def _write_manifest(rows: tuple[ManifestRow, ...]) -> None:
    _MANIFEST_PATH.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> int:
    """Refresh optional snapshots and regenerate the deterministic manifest."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="download fresh official indexes before generating the manifest",
    )
    options = parser.parse_args()
    legacy_rows = _load_legacy_rows()
    if options.refresh:
        _refresh_indexes()
    rows = generate_manifest(_read_indexes(), legacy_rows)
    _write_manifest(rows)
    _ = sys.stdout.write(
        "generated "
        f"{sum(row['product'] == 'claude-code' for row in rows)} Claude Code and "
        f"{sum(row['product'] == 'codex' for row in rows)} Codex sources"
        "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
