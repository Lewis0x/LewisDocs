# Copyright 2026
# ruff: noqa: INP001
"""Tests for strict validation of the AI manifest contract."""

from __future__ import annotations

import copy
import json
from collections.abc import Callable
from pathlib import Path
from typing import cast

import pytest
from pydantic import ValidationError

from scripts.ai.errors import AIAgentError, ErrorCode
from scripts.ai.manifest import load_sources
from scripts.ai.source_index import generate_manifest
from scripts.ai.types import FetchedPage, SourceId, SourceManifest

ROOT = Path(__file__).resolve().parents[2]
SOURCES_FILE = ROOT / "source-ai" / "sources.yaml"
INDEX_ROOT = ROOT / "source-ai" / "indexes"
MANIFEST_SIZE = 303

ManifestRow = dict[str, str]
Mutation = Callable[[list[ManifestRow]], None]


def _base_rows() -> list[ManifestRow]:
    """Load the fixture manifest as string-valued rows."""
    loaded = cast("object", json.loads(SOURCES_FILE.read_text(encoding="utf-8")))
    if not isinstance(loaded, list):
        message = "sources fixture must be a list"
        raise TypeError(message)
    payload = cast("list[object]", loaded)
    rows: list[ManifestRow] = []
    for row in payload:
        if not isinstance(row, dict):
            message = "sources fixture rows must be mappings"
            raise TypeError(message)
        typed_row = cast("dict[str, object]", row)
        mapping: dict[str, str] = {}
        for key, value in typed_row.items():
            if not isinstance(value, str):
                message = "sources fixture rows must map strings"
                raise TypeError(message)
            mapping[key] = value
        rows.append(mapping)
    return rows


def _write_rows(path: Path, rows: list[ManifestRow]) -> None:
    """Write rows to the temporary fixture path."""
    _ = path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")


def _expect_manifest_error(mutated_rows: list[ManifestRow], tmp_path: Path) -> None:
    """Assert that a bad manifest raises a manifest-code error."""
    mutated_file = tmp_path / "sources.yaml"
    _write_rows(mutated_file, mutated_rows)
    with pytest.raises(AIAgentError) as exc_info:
        _ = load_sources(mutated_file)
    assert exc_info.value.code == ErrorCode.MANIFEST_INVALID  # noqa: S101


def test_load_sources_happy_path() -> None:
    """Validate parsing of the canonical manifest."""
    manifest = load_sources(SOURCES_FILE)
    assert isinstance(manifest, SourceManifest)  # noqa: S101
    assert len(manifest.root) == MANIFEST_SIZE  # noqa: S101
    expected_ids = [row["id"] for row in _base_rows()]
    assert [source.id for source in manifest.root] == expected_ids  # noqa: S101


def _mutate_missing_field(rows: list[ManifestRow]) -> None:
    _ = rows[0].pop("title")


def _mutate_unknown_field(rows: list[ManifestRow]) -> None:
    rows[0]["unexpected"] = "value"


def _mutate_empty_string(rows: list[ManifestRow]) -> None:
    rows[0]["title"] = ""


def _mutate_duplicate_id(rows: list[ManifestRow]) -> None:
    rows[1]["id"] = rows[0]["id"]


def _mutate_duplicate_product_slug(rows: list[ManifestRow]) -> None:
    rows[1]["product"] = rows[0]["product"]
    rows[1]["slug"] = rows[0]["slug"]
    rows[1]["id"] = f"{rows[1]['product']}/{rows[1]['slug']}"


def _mutate_http_canonical_url(rows: list[ManifestRow]) -> None:
    rows[0]["canonical_url"] = "http://code.claude.com/docs/en/quickstart"


def _mutate_http_fetch_url(rows: list[ManifestRow]) -> None:
    rows[0]["fetch_url"] = "http://code.claude.com/docs/en/quickstart.md"


def _mutate_unsafe_slug(rows: list[ManifestRow]) -> None:
    rows[0]["slug"] = "../quickstart"
    rows[0]["id"] = "claude-code/../quickstart"


def _mutate_count_9(rows: list[ManifestRow]) -> None:
    _ = rows.pop()


def _mutate_count_11(rows: list[ManifestRow]) -> None:
    rows.append(
        {
            "id": "codex/extras",
            "product": "codex",
            "slug": "extras",
            "title": "Extra Source",
            "canonical_url": "https://learn.chatgpt.com/docs/extras",
            "fetch_url": "https://learn.chatgpt.com/docs/extras.md",
            "fetch_format": "markdown",
            "owner": "OpenAI",
        }
    )


def _mutate_split_4_6(rows: list[ManifestRow]) -> None:
    rows[0]["product"] = "codex"
    rows[0]["id"] = "codex/quickstart"
    rows[0]["canonical_url"] = "https://learn.chatgpt.com/docs/quickstart"
    rows[0]["fetch_url"] = "https://learn.chatgpt.com/docs/quickstart.md"
    rows[0]["owner"] = "OpenAI"


MUTATIONS: list[tuple[str, Mutation]] = [
    ("missing_field", _mutate_missing_field),
    ("unknown_field", _mutate_unknown_field),
    ("empty_string", _mutate_empty_string),
    ("duplicate_id", _mutate_duplicate_id),
    ("duplicate_product_slug", _mutate_duplicate_product_slug),
    ("http_canonical_url", _mutate_http_canonical_url),
    ("http_fetch_url", _mutate_http_fetch_url),
    ("unsafe_slug", _mutate_unsafe_slug),
    ("count_9", _mutate_count_9),
    ("count_11", _mutate_count_11),
    ("split_4_6", _mutate_split_4_6),
]


@pytest.mark.parametrize(
    "mutator",
    [mutator for _, mutator in MUTATIONS],
    ids=[name for name, _ in MUTATIONS],
)
def test_load_sources_rejects_mutations(
    mutator: Mutation,
    tmp_path: Path,
) -> None:
    """Mutation matrix: each invalid row should raise manifest-invalid."""
    rows = copy.deepcopy(_base_rows())
    mutator(rows)
    _expect_manifest_error(rows, tmp_path)


def test_fetched_page_preserves_text_boundaries() -> None:
    """Verify response text is preserved exactly while rejecting whitespace-only text."""
    raw_text = "  \r\n  heading\r\n\r\n  body  \r\n"
    page = FetchedPage(
        source_id=SourceId("claude-code/quickstart"),
        final_url="https://code.claude.com/docs/en/quickstart",
        content_type="text/markdown",
        text=raw_text,
    )
    assert page.text == raw_text  # noqa: S101

    with pytest.raises(ValidationError) as exc_info:
        _ = FetchedPage(
            source_id=SourceId("claude-code/quickstart"),
            final_url="https://code.claude.com/docs/en/quickstart",
            content_type="text/markdown",
            text=" \r\n  \t  ",
        )
    assert "non-whitespace" in str(exc_info.value)  # noqa: S101


def test_committed_manifest_is_generated_from_official_index_snapshots() -> None:
    """Keep every committed row tied to the complete official index snapshots."""
    rows = _base_rows()
    generated = generate_manifest(
        {
            "claude-code": (INDEX_ROOT / "claude-code.txt").read_text(encoding="utf-8"),
            "codex": (INDEX_ROOT / "codex.txt").read_text(encoding="utf-8"),
        },
        cast("tuple[ManifestRow, ...]", tuple(rows)),
    )
    assert list(generated) == rows  # noqa: S101
