# Copyright 2026
# ruff: noqa: INP001,PLR2004,S101

"""Internal AI build inventory verification tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.ai.errors import AIAgentError, ErrorCode
from scripts.ai.manifest import load_sources
from scripts.ai.verify_build import VerifyBuildOptions, verify_dist

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "source-ai" / "sources.yaml"


def _routes() -> tuple[str, ...]:
    manifest = load_sources(MANIFEST_PATH)
    source_routes = tuple(
        f"/ai/{lang}/{source.product}/{source.slug}"
        for source in manifest.root
        for lang in ("en", "zh-CN")
    )
    return (*source_routes, "/ai/zh-CN/learn/claude-code", "/ai/zh-CN/learn/codex")


def _install_dist(dist: Path, routes: tuple[str, ...], *, labels: bool = True) -> None:
    for route in routes:
        path = dist / f"{route.removeprefix('/')}.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        _ = path.write_text("<html></html>\n", encoding="utf-8")
    document_ids = {str(index): f"{route}#section" for index, route in enumerate(routes)}
    stored_fields: dict[str, dict[str, str | list[str]]] = {
        str(index): {
            "title": (
                ("EN · Synthetic" if "/en/" in route else "中文 · 合成") if labels else "Synthetic"
            ),
            "titles": [],
        }
        for index, route in enumerate(routes)
    }
    payload = json.dumps(
        {
            "documentCount": len(routes),
            "nextId": len(routes),
            "documentIds": document_ids,
            "storedFields": stored_fields,
            "index": [['"', {}]],
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )
    chunk = dist / "assets" / "chunks" / "@localSearchIndexroot.test.js"
    chunk.parent.mkdir(parents=True)
    escaped_payload = payload.replace("\\", "\\\\")
    _ = chunk.write_text(
        f"const t=`{escaped_payload}`;export{{t as default}};\n",
        encoding="utf-8",
    )


def _options(tmp_path: Path) -> VerifyBuildOptions:
    return VerifyBuildOptions(
        repo_root=REPO_ROOT,
        dist_root=tmp_path / "dist",
        manifest_path=MANIFEST_PATH,
    )


def test_verify_dist_accepts_exact_html_and_search_inventory(tmp_path: Path) -> None:
    """Given exact HTML/search routes, when verified, then the internal build passes."""
    # Given
    options = _options(tmp_path)
    _install_dist(options.dist_root, _routes())

    # When
    verify_dist(options)

    # Then
    assert len(tuple((options.dist_root / "ai").rglob("*.html"))) == 22


@pytest.mark.parametrize("mutation", ["missing_html", "extra_html", "missing_search", "labels"])
def test_verify_dist_rejects_incomplete_or_extra_inventory(
    tmp_path: Path,
    mutation: str,
) -> None:
    """Given one inventory defect, when verified, then validation fails."""
    # Given
    options = _options(tmp_path)
    routes = list(_routes())
    labels = mutation != "labels"
    search_routes = tuple(routes[:-1]) if mutation == "missing_search" else tuple(routes)
    _install_dist(options.dist_root, search_routes, labels=labels)
    if mutation == "missing_search":
        missing = routes[-1]
        path = options.dist_root / f"{missing.removeprefix('/')}.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        _ = path.write_text("<html></html>\n", encoding="utf-8")
    if mutation == "extra_html":
        extra = options.dist_root / "ai" / "en" / "codex" / "extra.html"
        extra.parent.mkdir(parents=True, exist_ok=True)
        _ = extra.write_text("<html></html>\n", encoding="utf-8")
    if mutation == "missing_html":
        absent = options.dist_root / f"{routes[-1].removeprefix('/')}.html"
        if absent.exists():
            absent.unlink()

    # When / Then
    with pytest.raises(AIAgentError) as exc_info:
        verify_dist(options)
    assert exc_info.value.code == ErrorCode.VALIDATION_FAILED
