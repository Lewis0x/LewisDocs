# ruff: noqa: CPY001, D100, D103, INP001, S101, S607, TC003

from __future__ import annotations

import json
import subprocess
from contextlib import AbstractContextManager
from hashlib import sha256
from pathlib import Path

import httpx2
import pytest
from pydantic import ValidationError

from scripts.ai import sync
from scripts.ai.errors import AIAgentError, ErrorCode, TranslationFailureReason
from scripts.ai.http_client import create_http_client
from scripts.ai.kimi import TranslationInput, translate_markdown
from scripts.ai.manifest import load_sources
from scripts.ai.snapshot import RealFileOps, tree_snapshot
from scripts.ai.sync import (
    PageSyncResult,
    SyncDeps,
    SyncOptions,
    SyncReport,
    run_sync,
    validate_content_root,
)
from scripts.ai.types import SourceId
from tests.ai.fixture_support import (
    FaultFileOps,
    install_content,
    install_learning,
    normalized_pages,
    transport_for,
)

ROOT = Path(__file__).resolve().parents[2]
FAULTS = (
    "candidate:en",
    "candidate:zh-CN",
    "next:en",
    "next:zh-CN",
    "rename:en-live-to-backup",
    "rename:zh-CN-live-to-backup",
    "rename:en-next-to-live",
    "rename:zh-CN-next-to-live",
    "report:temp-write",
    "report:replace",
    "cleanup",
)


def _page_result(
    *,
    source_id: str = "claude-code/quickstart",
    changed: bool = False,
) -> PageSyncResult:
    return PageSyncResult(
        source_id=SourceId(source_id),
        old_sha256="b" * 64 if changed else "a" * 64,
        new_sha256="a" * 64,
        changed=changed,
        translated=changed,
        result_code="UPDATED" if changed else "NO_CHANGES",
    )


def _report(*pages: PageSyncResult) -> SyncReport:
    return SyncReport(
        result="updated" if any(page.changed for page in pages) else "no_changes",
        pages=pages,
    )


def test_sync_main_prints_no_changes_then_canonical_report(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = _report(_page_result())
    received: list[tuple[SyncOptions, SyncDeps]] = []

    def fake_run(options: SyncOptions, deps: SyncDeps) -> SyncReport:
        received.append((options, deps))
        return expected

    monkeypatch.setattr(sync, "run_sync", fake_run)
    monkeypatch.setenv("AI_CONTENT_ROOT", "ignored-override")
    monkeypatch.delenv("MOONSHOT_API_KEY", raising=False)

    exit_code = sync.main()

    stdout, stderr = capsys.readouterr()
    lines = stdout.splitlines()
    assert exit_code == 0
    assert stderr == ""
    assert lines[0] == "no changes"
    assert json.loads(lines[1]) == expected.model_dump(mode="json")
    assert len(received) == 1
    options, deps = received[0]
    assert options.repo_root == ROOT
    assert options.content_root == ROOT / "source-ai" / "content"
    assert options.staging_root == ROOT / ".ai-local" / "staging"
    assert options.manifest_path == ROOT / "source-ai" / "sources.yaml"
    assert options.report_path == ROOT / ".ai-local" / "report.json"
    assert deps.client_factory is create_http_client
    assert deps.translator is translate_markdown
    assert isinstance(deps.file_ops, RealFileOps)


def test_sync_main_prints_stable_changed_table_then_canonical_report(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = _report(
        _page_result(source_id="claude-code/quickstart", changed=True),
        _page_result(source_id="codex/cli"),
    )

    def fake_run(options: SyncOptions, deps: SyncDeps) -> SyncReport:
        del options, deps
        return expected

    monkeypatch.setattr(sync, "run_sync", fake_run)

    exit_code = sync.main()

    stdout, stderr = capsys.readouterr()
    assert exit_code == 0
    assert stderr == ""
    assert "source_id" in stdout
    assert "old_sha256" in stdout
    assert "new_sha256" in stdout
    assert "result_code" in stdout
    assert stdout.index("claude-code/quickstart") < stdout.index("codex/cli")
    assert json.loads(stdout.splitlines()[-1]) == expected.model_dump(mode="json")
    assert "\x1b" not in stdout


@pytest.mark.parametrize(
    ("code", "source_id", "exit_code"),
    [
        (ErrorCode.MANIFEST_INVALID, None, 2),
        (ErrorCode.FETCH_FAILED, SourceId("claude-code/quickstart"), 3),
        (ErrorCode.KEY_REQUIRED, SourceId("claude-code/quickstart"), 4),
        (ErrorCode.TRANSLATION_FAILED, SourceId("claude-code/quickstart"), 5),
        (ErrorCode.VALIDATION_FAILED, None, 6),
        (ErrorCode.WRITE_FAILED, None, 7),
    ],
)
def test_sync_main_maps_errors_to_safe_single_line_output(
    code: ErrorCode,
    source_id: SourceId | None,
    exit_code: int,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sentinel = "process-only-secret-sentinel"

    def failing_run(options: SyncOptions, deps: SyncDeps) -> SyncReport:
        del options, deps
        raise AIAgentError(code=code, message=f"unsafe {sentinel}", source_id=source_id)

    monkeypatch.setattr(sync, "run_sync", failing_run)

    actual_exit = sync.main()

    stdout, stderr = capsys.readouterr()
    assert actual_exit == exit_code
    assert stderr == ""
    assert stdout.count("\n") == 1
    assert f"code={code}" in stdout
    assert f"source_id={source_id if source_id is not None else '-'}" in stdout
    assert sentinel not in stdout
    assert "Traceback" not in stdout


def test_sync_main_includes_fixed_translation_failure_reason(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sentinel = "unsafe-provider-detail"

    def failing_run(options: SyncOptions, deps: SyncDeps) -> SyncReport:
        del options, deps
        raise AIAgentError(
            code=ErrorCode.TRANSLATION_FAILED,
            message=sentinel,
            source_id=SourceId("claude-code/quickstart"),
            reason=TranslationFailureReason.PROVIDER_AUTH,
        )

    monkeypatch.setattr(sync, "run_sync", failing_run)

    actual_exit = sync.main()

    stdout, stderr = capsys.readouterr()
    assert actual_exit == 5  # noqa: PLR2004
    assert stderr == ""
    assert stdout == (
        "code=TRANSLATION_FAILED source_id=claude-code/quickstart "
        "message=translation failed reason=provider_auth\n"
    )
    assert sentinel not in stdout


@pytest.mark.parametrize("content_root", [None, "", "relative/content", "D:/other/content"])
def test_sync_main_uses_fixed_public_content_root(
    content_root: str | None,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    received: list[SyncOptions] = []

    def fake_run(options: SyncOptions, deps: SyncDeps) -> SyncReport:
        del deps
        received.append(options)
        return _report(_page_result())

    monkeypatch.setattr(sync, "run_sync", fake_run)
    if content_root is None:
        monkeypatch.delenv("AI_CONTENT_ROOT", raising=False)
    else:
        monkeypatch.setenv("AI_CONTENT_ROOT", content_root)

    exit_code = sync.main()

    stdout, stderr = capsys.readouterr()
    assert exit_code == 0
    assert stderr == ""
    assert len(received) == 1
    assert received[0].content_root == ROOT / "source-ai" / "content"
    assert stdout.startswith("no changes\n")


def _unreachable_translator(client: httpx2.Client, request: TranslationInput) -> str:
    del client, request
    pytest.fail("translator must not be called")


def test_sync_models_reject_inconsistent_page_and_report_results() -> None:
    with pytest.raises(ValidationError):
        _ = PageSyncResult(
            source_id=SourceId("claude-code/quickstart"),
            old_sha256=None,
            new_sha256="a" * 64,
            changed=False,
            translated=True,
            result_code="NO_CHANGES",
        )

    changed = PageSyncResult(
        source_id=SourceId("claude-code/quickstart"),
        old_sha256="b" * 64,
        new_sha256="a" * 64,
        changed=True,
        translated=True,
        result_code="UPDATED",
    )
    with pytest.raises(ValidationError):
        _ = SyncReport(result="no_changes", pages=(changed,))
    with pytest.raises(ValidationError):
        _ = SyncReport.model_validate({"result": "updated", "pages": (), "extra": True})
    with pytest.raises(ValidationError):
        changed.result_code = "NO_CHANGES"


def test_run_sync_leaves_accepted_content_unchanged_when_all_hashes_match(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest_path = ROOT / "source-ai" / "sources.yaml"
    manifest = load_sources(manifest_path)
    content = tmp_path / "private"
    pages = normalized_pages(manifest)
    install_content(content, pages)
    before = tree_snapshot(content)
    report_path = tmp_path / "report.json"
    _ = report_path.write_bytes(b"prior report\n")
    translated: list[SourceId] = []

    def translate(client: httpx2.Client, request: TranslationInput) -> str:
        del client
        translated.append(request.source_id)
        return "# 不应翻译\n"

    monkeypatch.delenv("MOONSHOT_API_KEY", raising=False)
    result = run_sync(
        SyncOptions(
            repo_root=ROOT,
            content_root=content,
            staging_root=tmp_path / "stage",
            manifest_path=manifest_path,
            report_path=report_path,
        ),
        SyncDeps(
            client_factory=lambda: create_http_client(transport_for(manifest)),
            translator=translate,
            file_ops=RealFileOps(),
        ),
    )

    assert result.result == "no_changes"
    assert translated == []
    assert tree_snapshot(content) == before
    assert report_path.read_bytes().endswith(b"\n")
    assert sha256(report_path.read_bytes()).hexdigest() != sha256(b"prior report\n").hexdigest()


def test_run_sync_translates_only_the_changed_page_and_preserves_other_pair_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest_path = ROOT / "source-ai" / "sources.yaml"
    manifest = load_sources(manifest_path)
    content = tmp_path / "private"
    install_content(content, normalized_pages(manifest))
    unchanged = manifest.root[1]
    before_en = (content / "en" / unchanged.product / f"{unchanged.slug}.md").read_bytes()
    before_zh = (content / "zh-CN" / unchanged.product / f"{unchanged.slug}.md").read_bytes()
    changed_id = manifest.root[0].id
    calls: list[SourceId] = []

    def translate(client: httpx2.Client, request: TranslationInput) -> str:
        del client
        calls.append(request.source_id)
        return f"# 中文 {request.source_id}\n\n已更新。\n"

    sentinel = "process-only-secret-sentinel"
    monkeypatch.setenv("MOONSHOT_API_KEY", sentinel)
    result = run_sync(
        SyncOptions(
            repo_root=ROOT,
            content_root=content,
            staging_root=tmp_path / "stage",
            manifest_path=manifest_path,
            report_path=tmp_path / "report.json",
        ),
        SyncDeps(
            client_factory=lambda: create_http_client(transport_for(manifest, changed_id)),
            translator=translate,
            file_ops=RealFileOps(),
        ),
    )

    assert result.result == "updated"
    assert calls == [changed_id]
    assert (content / "en" / unchanged.product / f"{unchanged.slug}.md").read_bytes() == before_en
    assert (
        content / "zh-CN" / unchanged.product / f"{unchanged.slug}.md"
    ).read_bytes() == before_zh
    assert sentinel.encode("utf-8") not in (tmp_path / "report.json").read_bytes()


@pytest.mark.parametrize("relative", [".", "source-ai", "docs", "project-docs"])
def test_private_roots_inside_the_repository_are_rejected_before_network(
    relative: str,
    tmp_path: Path,
) -> None:
    options = SyncOptions(
        repo_root=ROOT,
        content_root=(ROOT / relative).resolve(),
        staging_root=tmp_path / "stage",
        manifest_path=tmp_path / "missing.json",
        report_path=tmp_path / "report.json",
    )

    with pytest.raises(AIAgentError) as exc_info:
        _ = validate_content_root(options)

    assert exc_info.value.code == ErrorCode.VALIDATION_FAILED


def test_fixed_public_content_root_inside_repository_is_accepted(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    content = repo / "source-ai" / "content"
    content.mkdir(parents=True)
    options = SyncOptions(
        repo_root=repo,
        content_root=content,
        staging_root=repo / ".ai-local" / "stage",
        manifest_path=repo / "source-ai" / "sources.yaml",
        report_path=repo / ".ai-local" / "report.json",
    )

    assert validate_content_root(options) == content.resolve()


def test_private_root_rejects_force_tracked_ignored_content_before_client_creation(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _ = (repo / ".gitignore").write_text("/.ai-content/\n", encoding="utf-8")
    _ = subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    allowed = repo / ".ai-content"
    allowed.mkdir()
    options = SyncOptions(
        repo_root=repo,
        content_root=allowed,
        staging_root=tmp_path / "stage",
        manifest_path=tmp_path / "missing.json",
        report_path=tmp_path / "report.json",
    )

    assert validate_content_root(options) == allowed.resolve()
    assert (
        validate_content_root(options.model_copy(update={"content_root": allowed / "child"}))
        == (allowed / "child").resolve()
    )

    tracked = allowed / "tracked.txt"
    _ = tracked.write_text("tracked\n", encoding="utf-8")
    _ = subprocess.run(["git", "add", "-f", ".ai-content/tracked.txt"], cwd=repo, check=True)
    clients: list[str] = []

    def factory() -> AbstractContextManager[httpx2.Client]:
        clients.append("created")
        pytest.fail("private-root rejection must precede client creation")

    with pytest.raises(AIAgentError) as exc_info:
        _ = run_sync(
            options,
            SyncDeps(
                client_factory=factory, translator=_unreachable_translator, file_ops=RealFileOps()
            ),
        )

    assert exc_info.value.code == ErrorCode.VALIDATION_FAILED
    assert clients == []


def test_noop_rejects_report_inside_learning_tree_before_network_or_writes(
    tmp_path: Path,
) -> None:
    manifest_path = ROOT / "source-ai" / "sources.yaml"
    manifest = load_sources(manifest_path)
    content = tmp_path / "private"
    install_content(content, normalized_pages(manifest))
    learn_before = tree_snapshot(content / "learn")
    clients: list[str] = []

    def factory() -> AbstractContextManager[httpx2.Client]:
        clients.append("created")
        pytest.fail("support-path rejection must precede client creation")

    with pytest.raises(AIAgentError) as exc_info:
        _ = run_sync(
            SyncOptions(
                repo_root=ROOT,
                content_root=content,
                staging_root=tmp_path / "stage",
                manifest_path=manifest_path,
                report_path=content / "learn" / "report.json",
            ),
            SyncDeps(
                client_factory=factory, translator=_unreachable_translator, file_ops=RealFileOps()
            ),
        )

    assert exc_info.value.code == ErrorCode.VALIDATION_FAILED
    assert clients == []
    assert tree_snapshot(content / "learn") == learn_before


def test_run_sync_requires_a_nonempty_key_only_after_a_detected_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest_path = ROOT / "source-ai" / "sources.yaml"
    manifest = load_sources(manifest_path)
    content = tmp_path / "private"
    install_content(content, normalized_pages(manifest))
    before = tree_snapshot(content)
    monkeypatch.setenv("MOONSHOT_API_KEY", " \t")

    def translate(client: httpx2.Client, request: TranslationInput) -> str:
        del client, request
        pytest.fail("translator must not be called without a key")

    with pytest.raises(AIAgentError) as exc_info:
        _ = run_sync(
            SyncOptions(
                repo_root=ROOT,
                content_root=content,
                staging_root=tmp_path / "stage",
                manifest_path=manifest_path,
                report_path=tmp_path / "report.json",
            ),
            SyncDeps(
                client_factory=lambda: create_http_client(
                    transport_for(manifest, manifest.root[0].id)
                ),
                translator=translate,
                file_ops=RealFileOps(),
            ),
        )

    assert exc_info.value.code == ErrorCode.KEY_REQUIRED
    assert exc_info.value.source_id == manifest.root[0].id
    assert tree_snapshot(content) == before


def test_initial_sync_translates_all_sources_and_creates_bilingual_trees(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest_path = ROOT / "source-ai" / "sources.yaml"
    manifest = load_sources(manifest_path)
    content = tmp_path / "private"
    install_learning(content, normalized_pages(manifest))
    translated: list[SourceId] = []

    def translate(client: httpx2.Client, request: TranslationInput) -> str:
        del client
        translated.append(request.source_id)
        return f"# 中文 {request.source_id}\n\n初始内容。\n"

    monkeypatch.setenv("MOONSHOT_API_KEY", "process-only-test-key")
    result = run_sync(
        SyncOptions(
            repo_root=ROOT,
            content_root=content,
            staging_root=tmp_path / "stage",
            manifest_path=manifest_path,
            report_path=tmp_path / "report.json",
        ),
        SyncDeps(
            client_factory=lambda: create_http_client(transport_for(manifest)),
            translator=translate,
            file_ops=RealFileOps(),
        ),
    )

    assert result.result == "updated"
    assert translated == [source.id for source in manifest.root]
    assert (content / "en").is_dir()
    assert (content / "zh-CN").is_dir()


@pytest.mark.parametrize("fault", ["report:temp-write", "report:replace", "cleanup"])
def test_noop_report_fault_restores_the_prior_report(
    fault: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest_path = ROOT / "source-ai" / "sources.yaml"
    manifest = load_sources(manifest_path)
    content = tmp_path / "private"
    install_content(content, normalized_pages(manifest))
    before = tree_snapshot(content)
    report_path = tmp_path / "report.json"
    prior = b"prior report\n"
    _ = report_path.write_bytes(prior)
    monkeypatch.delenv("MOONSHOT_API_KEY", raising=False)

    def translate(client: httpx2.Client, request: TranslationInput) -> str:
        del client, request
        pytest.fail("no-op must not translate")

    with pytest.raises(AIAgentError) as exc_info:
        _ = run_sync(
            SyncOptions(
                repo_root=ROOT,
                content_root=content,
                staging_root=tmp_path / "stage",
                manifest_path=manifest_path,
                report_path=report_path,
            ),
            SyncDeps(
                client_factory=lambda: create_http_client(transport_for(manifest)),
                translator=translate,
                file_ops=FaultFileOps(fault),
            ),
        )

    assert exc_info.value.code == ErrorCode.WRITE_FAILED
    assert tree_snapshot(content) == before
    assert report_path.read_bytes() == prior


def test_fetch_and_translation_failures_preserve_the_accepted_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest_path = ROOT / "source-ai" / "sources.yaml"
    manifest = load_sources(manifest_path)
    content = tmp_path / "private"
    install_content(content, normalized_pages(manifest))
    before = tree_snapshot(content)
    report_path = tmp_path / "report.json"

    def failing_fetch(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(status_code=503, request=request, content=b"synthetic")

    with pytest.raises(AIAgentError) as fetch_error:
        _ = run_sync(
            SyncOptions(
                repo_root=ROOT,
                content_root=content,
                staging_root=tmp_path / "fetch-stage",
                manifest_path=manifest_path,
                report_path=report_path,
            ),
            SyncDeps(
                client_factory=lambda: create_http_client(httpx2.MockTransport(failing_fetch)),
                translator=_unreachable_translator,
                file_ops=RealFileOps(),
            ),
        )

    assert fetch_error.value.code == ErrorCode.FETCH_FAILED
    assert tree_snapshot(content) == before

    def failing_translate(client: httpx2.Client, request: TranslationInput) -> str:
        del client
        raise AIAgentError(
            code=ErrorCode.TRANSLATION_FAILED,
            message="synthetic translation failure",
            source_id=request.source_id,
        )

    monkeypatch.setenv("MOONSHOT_API_KEY", "process-only-test-key")
    with pytest.raises(AIAgentError) as translation_error:
        _ = run_sync(
            SyncOptions(
                repo_root=ROOT,
                content_root=content,
                staging_root=tmp_path / "translation-stage",
                manifest_path=manifest_path,
                report_path=report_path,
            ),
            SyncDeps(
                client_factory=lambda: create_http_client(
                    transport_for(manifest, manifest.root[0].id)
                ),
                translator=failing_translate,
                file_ops=RealFileOps(),
            ),
        )

    assert translation_error.value.code == ErrorCode.TRANSLATION_FAILED
    assert tree_snapshot(content) == before


@pytest.mark.parametrize("fault", FAULTS)
def test_run_sync_restores_content_report_and_learning_tree_for_each_write_fault(
    fault: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest_path = ROOT / "source-ai" / "sources.yaml"
    manifest = load_sources(manifest_path)
    content = tmp_path / "private"
    install_content(content, normalized_pages(manifest))
    report_path = tmp_path / "report.json"
    prior_report = b"prior report\n"
    _ = report_path.write_bytes(prior_report)
    before = tree_snapshot(content)
    learning_before = tree_snapshot(content / "learn")
    changed_id = manifest.root[0].id

    def translate(client: httpx2.Client, request: TranslationInput) -> str:
        del client, request
        return "# 中文\n\n更新。\n"

    monkeypatch.setenv("MOONSHOT_API_KEY", "process-only-test-key")
    with pytest.raises(AIAgentError) as exc_info:
        _ = run_sync(
            SyncOptions(
                repo_root=ROOT,
                content_root=content,
                staging_root=tmp_path / "stage",
                manifest_path=manifest_path,
                report_path=report_path,
            ),
            SyncDeps(
                client_factory=lambda: create_http_client(transport_for(manifest, changed_id)),
                translator=translate,
                file_ops=FaultFileOps(fault),
            ),
        )

    assert exc_info.value.code == ErrorCode.WRITE_FAILED
    assert tree_snapshot(content) == before
    assert tree_snapshot(content / "learn") == learning_before
    assert report_path.read_bytes() == prior_report
    stage = tmp_path / "stage"
    assert not stage.exists() or not tuple(stage.iterdir())
    assert not tuple(tmp_path.glob(".en-*-*"))
    assert not tuple(tmp_path.glob(".zh-CN-*-*"))
