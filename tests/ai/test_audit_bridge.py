# Copyright 2026
# ruff: noqa: INP001, S101, PLR2004

"""Tests for strict deep-audit ingestion into the repair pipeline."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, cast

import pytest

from scripts.ai.audit_bridge import (
    bridge_and_queue_deep_audit,
    bridge_deep_audit_report,
    map_reviewed_excerpts_to_raw,
    validate_deep_audit_report,
)
from scripts.ai.audit_coverage import (
    AuditCategory,
    AuditPass,
    derive_coverage_contract,
)
from scripts.ai.pipeline import PipelineState, PipelineStore
from scripts.ai.review_contract import (
    RepairIssueDraft,
    load_repair_ready_review,
    locate_candidate_span,
    sha256_path,
)

if TYPE_CHECKING:
    from pathlib import Path


def _write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(value, encoding="utf-8", newline="\n")


def test_exact_repair_span_preserves_boundary_whitespace() -> None:
    """Repair contracts must never normalize bytes in an exact candidate span."""
    exact = "  精确片段。\n"
    span = locate_candidate_span(f"# 标题\n\n{exact}", exact)
    draft = RepairIssueDraft(
        source_issue_refs=("issue-1",),
        severity="medium",
        category="semantic",
        location="opening",
        source_excerpt="Exact source.",
        candidate_span_text=exact,
        explanation="The exact span includes meaningful boundary whitespace.",
    )

    assert span.text == exact
    assert draft.candidate_span_text == exact


@pytest.mark.parametrize("language", ["text", "markdown", "md", "plaintext"])
def test_reader_facing_fence_span_is_repairable(language: str) -> None:
    """Prose examples may enter exact-span repair without opening code edits."""
    candidate = f"```{language}\nreader-facing sentence\n```\n"

    span = locate_candidate_span(candidate, "reader-facing sentence")

    assert span.text == "reader-facing sentence"


def test_executable_fence_span_remains_protected() -> None:
    """Executable snippets cannot enter the translation repair lane."""
    candidate = "```python\nprint('reader-facing sentence')\n```\n"

    with pytest.raises(ValueError, match="protected fenced code"):
        _ = locate_candidate_span(candidate, "reader-facing sentence")


def test_public_unique_span_must_also_be_unique_in_raw_candidate() -> None:
    """A bridgeability failure is explicit before a repair job is created."""
    with pytest.raises(ValueError, match="not unique in the raw candidate"):
        _ = map_reviewed_excerpts_to_raw(
            reviewed_source_excerpt="Unique source sentence.",
            reviewed_candidate_span="时间轴",
            raw_source="Unique source sentence.\n",
            raw_candidate="标题: 时间轴\n正文: 时间轴\n",
        )


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    source_id = "codex/test"
    raw_source = tmp_path / "source-ai/content/en/codex/test.md"
    raw_candidate = (
        tmp_path
        / ".ai-local/staging/dual-review-normalized/codex/test.md"
    )
    public_source = (
        tmp_path / ".ai-local/audit-materialized/codex/test/en.md"
    )
    public_candidate = (
        tmp_path / ".ai-local/audit-materialized/codex/test/zh-CN.md"
    )
    source_text = (
        "# Settings\n\n"
        "The client loads the configuration from the "
        "[settings file](https://example.com/settings).\n"
    )
    raw_candidate_text = (
        "---\n"
        "title: 设置\n"
        "---\n\n"
        "# 设置\n\n"
        "@[设置入口](#settings) 从错误的文件加载配置。\n"
    )
    public_candidate_text = raw_candidate_text.replace(
        "](#settings)",
        "](#设置)",
    )
    _write(raw_source, source_text)
    _write(raw_candidate, raw_candidate_text)
    _write(public_source, source_text)
    _write(public_candidate, public_candidate_text)

    manifest_path = tmp_path / ".ai-local/deep-audit.json"
    manifest = {
        "version": 1,
        "purpose": "strict-deep-audit-gap-fill",
        "entries": [
            {
                "source_id": source_id,
                "status": "prepared",
                "english_path": public_source.relative_to(tmp_path).as_posix(),
                "chinese_path": public_candidate.relative_to(tmp_path).as_posix(),
                "normalized_candidate_path": raw_candidate.relative_to(
                    tmp_path
                ).as_posix(),
                "producer": "test",
                "translation_model": "glm-5.2",
                "source_sha256": sha256_path(public_source),
                "candidate_sha256": sha256_path(public_candidate),
                "normalized_candidate_sha256": sha256_path(raw_candidate),
                "fenced_blocks_restored": 0,
            }
        ],
    }
    _write(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2))

    report_path = tmp_path / ".ai-local/reviews/terra/codex/test.json"
    report = {
        "source_id": source_id,
        "english_path": public_source.relative_to(tmp_path).as_posix(),
        "chinese_path": public_candidate.relative_to(tmp_path).as_posix(),
        "expected_source_sha256": sha256_path(public_source),
        "actual_source_sha256": sha256_path(public_source),
        "expected_candidate_sha256": sha256_path(public_candidate),
        "actual_candidate_sha256": sha256_path(public_candidate),
        "review_model": "gpt-5.6-terra",
        "verdict": "fail",
        "issues": [
            {
                "severity": "high",
                "category": "semantic_scope",
                "location": "opening paragraph",
                "source_excerpt": (
                    "The client loads the configuration from the settings file."
                ),
                "candidate_span_text": (
                    "@[设置入口](#设置) 从错误的文件加载配置。"
                ),
                "explanation": "The candidate reverses the configuration source.",
            }
        ],
        "reviewed_at": "2026-07-30T00:00:00Z",
        "eof_verification": {"complete_to_eof": True},
    }
    _write(report_path, json.dumps(report, ensure_ascii=False, indent=2))
    return manifest_path, report_path


def test_deep_audit_bridge_binds_report_and_maps_local_fragment(
    tmp_path: Path,
) -> None:
    """Legacy v1 reports remain compatible with deterministic span mapping."""
    manifest_path, report_path = _fixture(tmp_path)
    review = bridge_deep_audit_report(
        repo_root=tmp_path,
        manifest_path=manifest_path,
        report_path=report_path,
        source_id="codex/test",
        assigned_reviewer="gpt-5.6-terra",
    )

    assert review.version == 2
    assert review.source_report_evidence[0].sha256 == sha256_path(report_path)
    assert (
        review.issues[0].candidate_span.text
        == "@[设置入口](#settings) 从错误的文件加载配置。"
    )
    assert review.issues[0].source_excerpt == (
        "The client loads the configuration from the "
        "[settings file](https://example.com/settings)."
    )


def test_deep_audit_bridge_recovers_unique_markdown_line_wrapping(
    tmp_path: Path,
) -> None:
    """Public rendering may collapse a unique raw Markdown line break."""
    manifest_path, report_path = _fixture(tmp_path)
    raw_source = tmp_path / "source-ai/content/en/codex/test.md"
    _write(
        raw_source,
        (
            "The client loads the configuration\nfrom the "
            "[settings file](https://example.com/settings).\n"
        ),
    )

    review = bridge_deep_audit_report(
        repo_root=tmp_path,
        manifest_path=manifest_path,
        report_path=report_path,
        source_id="codex/test",
        assigned_reviewer="gpt-5.6-terra",
    )

    assert review.issues[0].source_excerpt == (
        "The client loads the configuration\nfrom the "
        "[settings file](https://example.com/settings)."
    )


def test_deep_audit_bridge_maps_title_prefix_before_frontmatter_gate(
    tmp_path: Path,
) -> None:
    """Public title prefixes map exactly, then the metadata repair gate blocks."""
    manifest_path, report_path = _fixture(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entry = manifest["entries"][0]
    raw_source = tmp_path / "source-ai/content/en/codex/test.md"
    raw_candidate = tmp_path / entry["normalized_candidate_path"]
    public_source = tmp_path / entry["english_path"]
    public_candidate = tmp_path / entry["chinese_path"]
    _write(
        raw_source,
        "---\ntitle: Codex Settings Overview\n---\n\n# Settings\n",
    )
    _write(
        raw_candidate,
        "---\ntitle: 设置概览\n---\n\n# 设置\n",
    )
    _write(
        public_source,
        "---\ntitle: EN · Codex Settings Overview\n---\n\n# Settings\n",
    )
    _write(
        public_candidate,
        "---\ntitle: 中文 · 设置概览\n---\n\n# 设置\n",
    )
    entry["source_sha256"] = sha256_path(public_source)
    entry["candidate_sha256"] = sha256_path(public_candidate)
    entry["normalized_candidate_sha256"] = sha256_path(raw_candidate)
    _write(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2))

    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["expected_source_sha256"] = sha256_path(public_source)
    report["actual_source_sha256"] = sha256_path(public_source)
    report["expected_candidate_sha256"] = sha256_path(public_candidate)
    report["actual_candidate_sha256"] = sha256_path(public_candidate)
    report["issues"] = [
        {
            "severity": "low",
            "category": "surface_frontmatter_h1",
            "location": "frontmatter title",
            "source_excerpt": "title: EN · Codex Settings Overview",
            "candidate_span_text": "title: 中文 · 设置概览",
            "explanation": "The translated title loses the product scope.",
        }
    ]
    _write(report_path, json.dumps(report, ensure_ascii=False, indent=2))

    with pytest.raises(ValueError, match="frontmatter"):
        _ = bridge_deep_audit_report(
            repo_root=tmp_path,
            manifest_path=manifest_path,
            report_path=report_path,
            source_id="codex/test",
            assigned_reviewer="gpt-5.6-terra",
        )


def test_deep_audit_bridge_coalesces_overlapping_repair_ranges(
    tmp_path: Path,
) -> None:
    """Nested findings become one provider span while retaining both reasons."""
    manifest_path, report_path = _fixture(tmp_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    outer = report["issues"][0]
    report["issues"].append(
        {
            "severity": "medium",
            "category": "surface_terminology",
            "location": "opening paragraph",
            "source_excerpt": "loads the configuration",
            "candidate_span_text": "从错误的文件加载配置",
            "explanation": "The nested terminology is inconsistent.",
        }
    )
    _write(report_path, json.dumps(report, ensure_ascii=False, indent=2))

    review = bridge_deep_audit_report(
        repo_root=tmp_path,
        manifest_path=manifest_path,
        report_path=report_path,
        source_id="codex/test",
        assigned_reviewer="gpt-5.6-terra",
    )

    assert len(review.issues) == 1
    issue = review.issues[0]
    assert issue.candidate_span.text == outer["candidate_span_text"].replace(
        "](#设置)",
        "](#settings)",
    )
    assert len(issue.source_issue_refs) == 2
    assert "reverses the configuration source" in issue.explanation
    assert "nested terminology is inconsistent" in issue.explanation


def test_deep_audit_bridge_rejects_ambiguous_exact_excerpt(
    tmp_path: Path,
) -> None:
    """A repeated short reviewer excerpt cannot select a repair target."""
    manifest_path, report_path = _fixture(tmp_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["issues"][0]["source_excerpt"] = "the"
    _write(report_path, json.dumps(report, ensure_ascii=False, indent=2))

    with pytest.raises(ValueError, match="not exact or uniquely"):
        _ = bridge_deep_audit_report(
            repo_root=tmp_path,
            manifest_path=manifest_path,
            report_path=report_path,
            source_id="codex/test",
            assigned_reviewer="gpt-5.6-terra",
        )


def test_v2_manifest_requires_symmetric_complete_coverage(
    tmp_path: Path,
) -> None:
    """The bridge selects the strict coverage schema only for v2 entries."""
    manifest_path, report_path = _fixture(tmp_path)
    manifest = cast(
        "dict[str, object]",
        json.loads(manifest_path.read_text(encoding="utf-8")),
    )
    entries = cast("list[dict[str, object]]", manifest["entries"])
    entry = entries[0]
    english_path_value = str(entry["english_path"])
    chinese_path_value = str(entry["chinese_path"])
    public_source = tmp_path / english_path_value
    public_candidate = tmp_path / chinese_path_value
    contract = derive_coverage_contract(
        source_id="codex/test",
        english_path=public_source,
        chinese_path=public_candidate,
        english_path_value=english_path_value,
        chinese_path_value=chinese_path_value,
    )
    entry["audit_contract_version"] = 2
    entry["coverage_contract"] = contract.model_dump(mode="json", by_alias=True)
    _write(
        manifest_path,
        json.dumps(manifest, ensure_ascii=False, indent=2),
    )
    report = {
        "version": 2,
        "audit_contract_version": 2,
        "source_id": "codex/test",
        "review_model": "gpt-5.6-terra",
        "verdict": "pass",
        "english_path": entry["english_path"],
        "chinese_path": entry["chinese_path"],
        "source_sha256": entry["source_sha256"],
        "candidate_sha256": entry["candidate_sha256"],
        "passes": [
            {"pass": item.value, "checked": True, "issue_count": 0}
            for item in AuditPass
        ],
        "categories": [
            {
                "pass": item.audit_pass,
                "category": item.category,
                "checked": True,
                "issue_count": 0,
            }
            for item in contract.mandatory_categories
        ],
        "sections": [
            {
                "section_id": item.section_id,
                "ordinal": item.ordinal,
                "heading": item.heading,
                "checked": True,
                "issue_count": 0,
            }
            for item in contract.sections
        ],
        "evidence": contract.evidence.model_dump(mode="json"),
        "issues": [],
    }
    _write(report_path, json.dumps(report, ensure_ascii=False, indent=2))

    validated = validate_deep_audit_report(
        repo_root=tmp_path,
        manifest_path=manifest_path,
        report_path=report_path,
        source_id="codex/test",
        assigned_reviewer="gpt-5.6-terra",
    )

    assert validated.verdict == "pass"
    assert tuple(AuditCategory) == tuple(
        AuditCategory(item.category)
        for item in contract.mandatory_categories
    )


def test_deep_audit_bridge_queues_one_canonical_repair(tmp_path: Path) -> None:
    """A verified report enters the canonical repair queue exactly once."""
    manifest_path, report_path = _fixture(tmp_path)
    store = PipelineStore(tmp_path / ".ai-local/pipeline-v1", tmp_path)
    repair_review_path = tmp_path / ".ai-local/repair-ready/codex/test.json"
    result = bridge_and_queue_deep_audit(
        store=store,
        manifest_path=manifest_path,
        report_path=report_path,
        repair_review_path=repair_review_path,
        source_id="codex/test",
        assigned_reviewer="gpt-5.6-terra",
        provider="glm",
        attempt_id="deep-audit-v1",
        actor="test",
    )
    repeated = bridge_and_queue_deep_audit(
        store=store,
        manifest_path=manifest_path,
        report_path=report_path,
        repair_review_path=repair_review_path,
        source_id="codex/test",
        assigned_reviewer="gpt-5.6-terra",
        provider="glm",
        attempt_id="deep-audit-v1",
        actor="test",
    )

    assert result.job.state == PipelineState.REPAIR_QUEUED
    assert repeated.job.job_id == result.job.job_id
    assert len(store.list_jobs()) == 1


def test_v2_repair_review_rejects_changed_source_report(tmp_path: Path) -> None:
    """The canonical bridge cannot outlive the detailed report it cites."""
    manifest_path, report_path = _fixture(tmp_path)
    review = bridge_deep_audit_report(
        repo_root=tmp_path,
        manifest_path=manifest_path,
        report_path=report_path,
        source_id="codex/test",
        assigned_reviewer="gpt-5.6-terra",
    )
    repair_review_path = tmp_path / ".ai-local/repair-ready/codex/test.json"
    repair_review_path.parent.mkdir(parents=True, exist_ok=True)
    _ = repair_review_path.write_text(
        review.model_dump_json(indent=2),
        encoding="utf-8",
    )
    _ = report_path.write_text("{}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="source audit report hash changed"):
        _ = load_repair_ready_review(repair_review_path, tmp_path)
