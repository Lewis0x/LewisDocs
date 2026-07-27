# ruff: noqa: CPY001,D100,D103,INP001,PLR2004,RUF001,S101

from __future__ import annotations

import json
import shutil
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict
from uuid import uuid4

import pytest
from pydantic import TypeAdapter

from scripts.ai.cad_paths import iter_cad_markdown
from scripts.ai.errors import AIAgentError, ErrorCode
from scripts.ai.http_client import create_http_client
from scripts.ai.manifest import load_sources
from scripts.ai.materialize import MaterializeOptions, materialize_ai
from scripts.ai.snapshot import RealFileOps, tree_snapshot
from scripts.ai.sync import SyncDeps, SyncOptions, run_sync
from tests.ai.fixture_support import FaultFileOps, install_content, normalized_pages, transport_for
from tests.ai.test_snapshot import FAULT_LABELS

if TYPE_CHECKING:
    import httpx2

    from scripts.ai.kimi import TranslationInput
    from scripts.ai.types import SourceId

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "source-ai" / "sources.yaml"
QUERY_PATH = ROOT / "tests" / "ai" / "fixtures" / "browser-queries.json"
SOURCE_IDS = (
    "claude-code/quickstart",
    "claude-code/memory",
    "claude-code/permissions",
    "claude-code/extensions",
    "claude-code/best-practices",
    "codex/cli",
    "codex/prompting",
    "codex/agents-md",
    "codex/approvals-security",
    "codex/customization",
)
ROUTES = frozenset(
    f"/ai/{language}/{source_id}" for source_id in SOURCE_IDS for language in ("en", "zh-CN")
) | frozenset(("/ai/zh-CN/learn/claude-code", "/ai/zh-CN/learn/codex"))


class _SearchQuery(TypedDict):
    query: str
    route: str
    label: str


class _CadQuery(TypedDict):
    source_route: str
    selector: str
    text: str
    target_route: str
    target_anchor: str


class _BrowserQueries(TypedDict):
    search: tuple[_SearchQuery, _SearchQuery]
    cad: _CadQuery


def _options(private: Path, temporary: Path) -> SyncOptions:
    return SyncOptions(
        repo_root=ROOT,
        content_root=private,
        staging_root=temporary / "staging",
        manifest_path=MANIFEST_PATH,
        report_path=temporary / "report.json",
    )


def _unreachable_translator(client: httpx2.Client, request: TranslationInput) -> str:
    del client, request
    pytest.fail("translator must not be called")


def test_ac1_ac2_ac7_exact_pairs_routes_links_learning_and_cad(tmp_path: Path) -> None:
    manifest = load_sources(MANIFEST_PATH)
    assert tuple(source.id for source in manifest.root) == SOURCE_IDS
    private = tmp_path / "private"
    install_content(private, normalized_pages(manifest))
    repository = tmp_path / "repository"
    routes = materialize_ai(
        MaterializeOptions(repository, private, repository / "docs" / "ai", MANIFEST_PATH)
    )
    assert len(routes) == 22
    assert {route.route for route in routes} == ROUTES
    for source in manifest.root:
        en = f"/ai/en/{source.product}/{source.slug}"
        zh = f"/ai/zh-CN/{source.product}/{source.slug}"
        assert next(route for route in routes if route.route == en).counterpart == zh
        assert next(route for route in routes if route.route == zh).counterpart == en
        assert f"ai_counterpart: {zh}" in (repository / "docs" / "ai" / f"{en[4:]}.md").read_text()
        assert f"ai_counterpart: {en}" in (repository / "docs" / "ai" / f"{zh[4:]}.md").read_text()
    for product in ("claude-code", "codex"):
        links = (private / "learn" / "zh-CN" / f"{product}.md").read_text(encoding="utf-8")
        assert links.count("](/ai/zh-CN/") == 5
        assert all(
            f"/ai/zh-CN/{product}/{source.slug}" in links
            for source in manifest.root
            if source.product == product
        )
    fixture = TypeAdapter(_BrowserQueries).validate_python(
        json.loads(QUERY_PATH.read_text(encoding="utf-8"))
    )
    assert fixture["search"] == (
        {
            "query": "synthetic permissions marker",
            "route": "/ai/en/claude-code/permissions",
            "label": "EN",
        },
        {"query": "合成权限标记", "route": "/ai/zh-CN/claude-code/permissions", "label": "中文"},
    )
    for query in fixture["search"]:
        page = repository / "docs" / "ai" / f"{query['route'][4:]}.md"
        page_text = page.read_text(encoding="utf-8")
        assert query["query"].casefold() in page_text.casefold()
        assert f"ai_search_label: {query['label']}" in page_text
    cad = fixture["cad"]
    assert cad["source_route"] == "/platforms/bricscad"
    assert cad["target_route"] == "/platforms/autocad"
    assert cad["target_anchor"] == "二、api-整体架构-六层金字塔"
    expected_link = f"[{cad['text']}]({cad['target_route']}#{cad['target_anchor']})"
    assert expected_link in (ROOT / "docs" / "platforms" / "bricscad.md").read_text()
    assert (
        "## 二、API 整体架构：六层金字塔"
        in (ROOT / "docs" / "platforms" / "autocad.md").read_text()
    )
    assert all(
        path.relative_to(ROOT / "docs").parts[0] != "ai"
        for path in iter_cad_markdown(ROOT / "docs")
    )


def test_materialize_allows_complete_english_preview_without_dead_counterparts(
    tmp_path: Path,
) -> None:
    """Publish all English sources while translated counterparts are still pending."""
    manifest = load_sources(MANIFEST_PATH)
    private = tmp_path / "private"
    pages = list(normalized_pages(manifest))
    markdown = (
        "# Synthetic claude-code/quickstart\n\n"
        "<Tip>Keep this reviewable guidance.</Tip>\n\n"
        '[<IconItem title="Review"><span slot="icon"><Plugin /></span>'
        "Review settings</IconItem>](https://example.test/settings)\n\n"
        "```md\n<Tip>literal example</Tip>\n```\n"
    )
    pages[0] = replace(
        pages[0],
        markdown=markdown,
        content_sha256=sha256(markdown.encode("utf-8")).hexdigest(),
    )
    install_content(private, tuple(pages))
    shutil.rmtree(private / "zh-CN")
    repository = tmp_path / "repository"

    routes = materialize_ai(
        MaterializeOptions(repository, private, repository / "docs" / "ai", MANIFEST_PATH)
    )

    assert len(routes) == len(SOURCE_IDS)
    assert all(route.lang == "en" and route.counterpart is None for route in routes)
    for source in manifest.root:
        page = repository / "docs" / "ai" / "en" / source.product / f"{source.slug}.md"
        assert page.is_file()
        assert "ai_counterpart:" not in page.read_text(encoding="utf-8")
    quickstart = (
        repository / "docs" / "ai" / "en" / "claude-code" / "quickstart.md"
    ).read_text(encoding="utf-8")
    assert "<Tip>Keep" not in quickstart
    assert "Keep this reviewable guidance." in quickstart
    assert "<span" not in quickstart
    assert "[Review settings](https://example.test/settings)" in quickstart
    assert "```md\n<Tip>literal example</Tip>\n```" in quickstart
    assert not (repository / "docs" / "ai" / "zh-CN").exists()


def test_ac3_noop_needs_no_key_or_translator_and_changes_no_private_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = load_sources(MANIFEST_PATH)
    private = tmp_path / "private"
    install_content(private, normalized_pages(manifest))
    before = tree_snapshot(private)
    monkeypatch.delenv("MOONSHOT_API_KEY", raising=False)
    report = run_sync(
        _options(private, tmp_path),
        SyncDeps(
            lambda: create_http_client(transport_for(manifest)),
            _unreachable_translator,
            RealFileOps(),
        ),
    )
    assert report.result == "no_changes"
    assert all(not item.changed and not item.translated for item in report.pages)
    assert tree_snapshot(private) == before
    assert not (tmp_path / "staging").exists()


def test_ac4_one_changed_pair_preserves_all_other_pair_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = load_sources(MANIFEST_PATH)
    private = tmp_path / "private"
    install_content(private, normalized_pages(manifest))
    before = tree_snapshot(private)
    changed = manifest.root[0]
    translated: list[SourceId] = []

    def translate(client: httpx2.Client, request: TranslationInput) -> str:
        del client
        source_id = request.source_id
        translated.append(source_id)
        return f"# 中文 {source_id}\n\n合成更新。\n"

    monkeypatch.setenv("MOONSHOT_API_KEY", f"synthetic-{uuid4().hex}")
    report = run_sync(
        _options(private, tmp_path),
        SyncDeps(
            lambda: create_http_client(transport_for(manifest, changed.id)),
            translate,
            RealFileOps(),
        ),
    )
    assert report.result == "updated"
    assert translated == [changed.id]
    assert sum(item.changed for item in report.pages) == 1
    after = tree_snapshot(private)
    unchanged = {
        item.path: item.sha256 for item in before.files if str(changed.slug) not in item.path
    }
    assert all(
        after_item.sha256 == digest
        for after_item in after.files
        if after_item.path in unchanged
        for digest in [unchanged[after_item.path]]
    )


@pytest.mark.parametrize("fault", FAULT_LABELS)
def test_ac5_every_write_fault_restores_accepted_snapshot(
    fault: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = load_sources(MANIFEST_PATH)
    private = tmp_path / "private"
    install_content(private, normalized_pages(manifest))
    before = tree_snapshot(private)
    monkeypatch.setenv("MOONSHOT_API_KEY", f"synthetic-{uuid4().hex}")

    def translate(client: httpx2.Client, request: TranslationInput) -> str:
        del client
        return f"# 中文 {request.source_id}\n\n合成更新。\n"

    with pytest.raises(AIAgentError) as error:
        _ = run_sync(
            _options(private, tmp_path),
            SyncDeps(
                lambda: create_http_client(transport_for(manifest, manifest.root[0].id)),
                translate,
                FaultFileOps(fault),
            ),
        )
    assert error.value.code == ErrorCode.WRITE_FAILED
    assert tree_snapshot(private) == before


def test_ac6_runtime_secret_sentinel_is_absent_from_outputs_and_owned_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = load_sources(MANIFEST_PATH)
    private = tmp_path / "private"
    install_content(private, normalized_pages(manifest))
    sentinel = uuid4().hex
    monkeypatch.setenv("MOONSHOT_API_KEY", sentinel)
    report = run_sync(
        _options(private, tmp_path),
        SyncDeps(
            lambda: create_http_client(transport_for(manifest)),
            _unreachable_translator,
            RealFileOps(),
        ),
    )
    captured = (tmp_path / "report.json").read_bytes()
    roots = (tmp_path, ROOT / "docs" / ".vitepress" / "dist")
    assert sentinel.encode() not in captured
    assert all(
        sentinel not in path.read_text(encoding="utf-8", errors="ignore")
        for root in roots
        if root.exists()
        for path in root.rglob("*")
        if path.is_file()
    )
    assert sentinel not in Path(__file__).read_text(encoding="utf-8")
    assert sentinel not in QUERY_PATH.read_text(encoding="utf-8")
    assert report.result == "no_changes"
