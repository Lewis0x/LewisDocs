# Copyright 2026
# ruff: noqa: INP001, S101

"""Tests for the deterministic deep-audit v2 coverage contract."""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, cast

import pytest
from pydantic import ValidationError

from scripts.ai.audit_coverage import (
    AuditCategory,
    AuditPass,
    CoverageIssue,
    DeepAuditCoverageContract,
    DeepAuditFindingReport,
    build_reviewer_contract_payload,
    build_reviewer_prompt,
    canonicalize_finding_excerpts,
    derive_coverage_contract,
    materialize_coverage_report,
    validate_coverage_report,
)

if TYPE_CHECKING:
    from pathlib import Path

SOURCE_ID = "codex/coverage-test"


def test_coverage_issue_preserves_exact_excerpt_whitespace() -> None:
    """Model-authored exact evidence must retain every boundary byte."""
    source_excerpt = "  Source line.\n"
    candidate_span = "  译文行。\n"
    issue = CoverageIssue.model_validate(
        {
            "issue_id": "exact-whitespace",
            "pass": "semantic",
            "category": "semantic_roles",
            "section_id": "preamble",
            "severity": "medium",
            "location": "opening",
            "source_excerpt": source_excerpt,
            "candidate_span_text": candidate_span,
            "explanation": "Boundary whitespace is part of the exact evidence.",
        }
    )

    assert issue.source_excerpt == source_excerpt
    assert issue.candidate_span_text == candidate_span


def _write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(value, encoding="utf-8", newline="\n")


def _contract(tmp_path: Path) -> tuple[DeepAuditCoverageContract, Path, Path]:
    english = tmp_path / ".ai-local/audit-materialized/codex/coverage-test/en.md"
    chinese = (
        tmp_path / ".ai-local/audit-materialized/codex/coverage-test/zh-CN.md"
    )
    _write(
        english,
        (
            "---\n"
            "title: Settings\n"
            "description: Configure the client\n"
            "---\n"
            "Official source\n\n"
            "# Settings\n\n"
            "Select `Open settings` in the UI.\n\n"
            "## Details\n\n"
            "The client loads [the file](https://example.test/settings).\n"
        ),
    )
    _write(
        chinese,
        (
            "---\n"
            "title: 设置\n"
            "description: 配置客户端\n"
            "---\n"
            "官方来源\n\n"
            "# 设置\n\n"
            "在界面中选择 `Open settings`。\n\n"
            "## 详情\n\n"
            "客户端加载[该文件](https://example.test/settings)。\n"
        ),
    )
    contract = derive_coverage_contract(
        source_id=SOURCE_ID,
        english_path=english,
        chinese_path=chinese,
        english_path_value=".ai-local/audit-materialized/codex/coverage-test/en.md",
        chinese_path_value=(
            ".ai-local/audit-materialized/codex/coverage-test/zh-CN.md"
        ),
    )
    return contract, english, chinese


def _report(
    contract: DeepAuditCoverageContract,
    *,
    verdict: str = "pass",
    issues: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    issue_values = issues or []
    pass_counts = {
        audit_pass.value: sum(
            issue["pass"] == audit_pass.value for issue in issue_values
        )
        for audit_pass in AuditPass
    }
    category_counts = {
        category.value: sum(
            issue["category"] == category.value for issue in issue_values
        )
        for category in AuditCategory
    }
    section_counts = {
        section.section_id: sum(
            issue["section_id"] == section.section_id
            for issue in issue_values
        )
        for section in contract.sections
    }
    return {
        "version": 2,
        "audit_contract_version": 2,
        "source_id": contract.source_id,
        "review_model": "gpt-5.6-terra",
        "verdict": verdict,
        "english_path": contract.english_path,
        "chinese_path": contract.chinese_path,
        "source_sha256": contract.source_sha256,
        "candidate_sha256": contract.candidate_sha256,
        "passes": [
            {
                "pass": audit_pass.value,
                "checked": True,
                "issue_count": pass_counts[audit_pass.value],
            }
            for audit_pass in AuditPass
        ],
        "categories": [
            {
                "pass": item.audit_pass,
                "category": item.category,
                "checked": True,
                "issue_count": category_counts[str(item.category)],
            }
            for item in contract.mandatory_categories
        ],
        "sections": [
            {
                "section_id": section.section_id,
                "ordinal": section.ordinal,
                "heading": section.heading,
                "checked": True,
                "issue_count": section_counts[section.section_id],
            }
            for section in contract.sections
        ],
        "evidence": contract.evidence.model_dump(mode="json"),
        "issues": issue_values,
    }


def _semantic_issue(
    contract: DeepAuditCoverageContract,
) -> dict[str, object]:
    details = next(
        section
        for section in contract.sections
        if section.english_heading == "Details"
    )
    return {
        "issue_id": "semantic-001",
        "pass": "semantic",
        "category": "semantic_subject_object",
        "section_id": details.section_id,
        "severity": "high",
        "location": "Details opening sentence",
        "source_excerpt": "The client loads",
        "candidate_span_text": "客户端加载",
        "explanation": "The actor and object must remain aligned.",
    }


def _findings(
    contract: DeepAuditCoverageContract,
    *,
    verdict: str = "pass",
    issues: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "version": 1,
        "audit_contract_version": 2,
        "source_id": contract.source_id,
        "review_model": "gpt-5.6-terra",
        "verdict": verdict,
        "checked_passes": [item.value for item in AuditPass],
        "checked_categories": [item.value for item in AuditCategory],
        "checked_section_ids": [
            item.section_id for item in contract.sections
        ],
        "reached_real_eof": True,
        "issues": issues or [],
    }


def _validate(
    report: object,
    contract: DeepAuditCoverageContract,
    english: Path,
    chinese: Path,
) -> None:
    _ = validate_coverage_report(
        report,
        contract=contract,
        assigned_reviewer="gpt-5.6-terra",
        english_path=english,
        chinese_path=chinese,
    )


def test_complete_pass_and_fail_reports_are_accepted(tmp_path: Path) -> None:
    """Both verdict paths require all passes, categories, and sections."""
    contract, english, chinese = _contract(tmp_path)
    _validate(_report(contract), contract, english, chinese)
    fail_report = _report(
        contract,
        verdict="fail",
        issues=[_semantic_issue(contract)],
    )

    _validate(fail_report, contract, english, chinese)


def test_compact_findings_materialize_canonical_evidence(
    tmp_path: Path,
) -> None:
    """Models report findings while local code expands deterministic fields."""
    contract, english, chinese = _contract(tmp_path)
    findings = DeepAuditFindingReport.model_validate(
        _findings(
            contract,
            verdict="fail",
            issues=[_semantic_issue(contract)],
        )
    )
    canonical = materialize_coverage_report(
        findings,
        contract=contract,
        assigned_reviewer="gpt-5.6-terra",
    )

    _validate(canonical, contract, english, chinese)
    assert canonical.evidence == contract.evidence
    assert len(canonical.sections) == len(contract.sections)


def test_compact_findings_reject_duplicate_candidate_spans(
    tmp_path: Path,
) -> None:
    """One repair span cannot be duplicated across audit categories."""
    contract, _english, _chinese = _contract(tmp_path)
    first = _semantic_issue(contract)
    second = deepcopy(first)
    second["issue_id"] = "semantic-002"
    second["category"] = "semantic_roles"

    with pytest.raises(ValidationError, match="same exact candidate span"):
        _ = DeepAuditFindingReport.model_validate(
            _findings(
                contract,
                verdict="fail",
                issues=[first, second],
            )
        )


def test_compact_findings_require_exact_section_ledger(
    tmp_path: Path,
) -> None:
    """The compact ledger still binds every expected section in order."""
    contract, _english, _chinese = _contract(tmp_path)
    value = _findings(contract)
    checked = cast("list[str]", value["checked_section_ids"])
    _ = checked.pop()
    findings = DeepAuditFindingReport.model_validate(value)

    with pytest.raises(ValueError, match="every contract section"):
        _ = materialize_coverage_report(
            findings,
            contract=contract,
            assigned_reviewer="gpt-5.6-terra",
        )


def test_compact_findings_recover_unique_markdown_line_wrap(
    tmp_path: Path,
) -> None:
    """Local code may restore whitespace only when the exact span is unique."""
    contract, english, chinese = _contract(tmp_path)
    english_text = english.read_text(encoding="utf-8")
    chinese_text = chinese.read_text(encoding="utf-8")
    _write(
        english,
        english_text.replace(
            "The client loads",
            "The client\nloads",
        ),
    )
    _write(chinese, chinese_text + "\nAlpha\nBeta\n")
    contract = derive_coverage_contract(
        source_id=SOURCE_ID,
        english_path=english,
        chinese_path=chinese,
        english_path_value=contract.english_path,
        chinese_path_value=contract.chinese_path,
    )
    issue = _semantic_issue(contract)
    issue["candidate_span_text"] = "AlphaBeta"
    findings = DeepAuditFindingReport.model_validate(
        _findings(contract, verdict="fail", issues=[issue])
    )

    canonicalized = canonicalize_finding_excerpts(
        findings,
        english_path=english,
        chinese_path=chinese,
    )

    assert canonicalized.issues[0].source_excerpt == "The client\nloads"
    assert canonicalized.issues[0].candidate_span_text == "Alpha\nBeta"
    canonical = materialize_coverage_report(
        canonicalized,
        contract=contract,
        assigned_reviewer="gpt-5.6-terra",
    )
    _validate(canonical, contract, english, chinese)


def test_compact_findings_reject_ambiguous_whitespace_recovery(
    tmp_path: Path,
) -> None:
    """Collapsed whitespace cannot silently choose between multiple spans."""
    contract, english, chinese = _contract(tmp_path)
    chinese_text = chinese.read_text(encoding="utf-8")
    _write(chinese, chinese_text + "\nAlpha\nBeta\n\nAl\nphaBeta\n")
    contract = derive_coverage_contract(
        source_id=SOURCE_ID,
        english_path=english,
        chinese_path=chinese,
        english_path_value=contract.english_path,
        chinese_path_value=contract.chinese_path,
    )
    issue = _semantic_issue(contract)
    issue["candidate_span_text"] = "AlphaBeta"
    findings = DeepAuditFindingReport.model_validate(
        _findings(contract, verdict="fail", issues=[issue])
    )

    with pytest.raises(ValueError, match="uniquely whitespace-equivalent"):
        _ = canonicalize_finding_excerpts(
            findings,
            english_path=english,
            chinese_path=chinese,
        )

def test_rejects_missing_or_duplicate_sections(tmp_path: Path) -> None:
    """A reviewer cannot skip, invent, duplicate, or reorder a section."""
    contract, english, chinese = _contract(tmp_path)
    missing = _report(contract)
    _ = cast("list[object]", missing["sections"]).pop(2)
    with pytest.raises(ValueError, match="missing"):
        _validate(missing, contract, english, chinese)

    duplicate = _report(contract)
    sections = cast("list[dict[str, object]]", duplicate["sections"])
    sections[2] = deepcopy(sections[1])
    with pytest.raises(ValueError, match="duplicate"):
        _validate(duplicate, contract, english, chinese)


def test_rejects_missing_category_and_issue_count_drift(tmp_path: Path) -> None:
    """Every mandatory category and every derived issue count is binding."""
    contract, english, chinese = _contract(tmp_path)
    missing = _report(contract)
    _ = cast("list[object]", missing["categories"]).pop()
    with pytest.raises(ValidationError):
        _validate(missing, contract, english, chinese)

    mismatch = _report(
        contract,
        verdict="warn",
        issues=[_semantic_issue(contract)],
    )
    categories = cast("list[dict[str, object]]", mismatch["categories"])
    target = next(
        item
        for item in categories
        if item["category"] == "semantic_subject_object"
    )
    target["issue_count"] = 0
    with pytest.raises(ValueError, match="issue_count"):
        _validate(mismatch, contract, english, chinese)


def test_rejects_wrong_hash_and_false_eof_evidence(tmp_path: Path) -> None:
    """Hashes and true-EOF evidence are recomputed from the reviewed files."""
    contract, english, chinese = _contract(tmp_path)
    wrong_hash = _report(contract)
    wrong_hash["candidate_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="Chinese hash"):
        _validate(wrong_hash, contract, english, chinese)

    wrong_eof = _report(contract)
    evidence = cast("dict[str, object]", wrong_eof["evidence"])
    chinese_evidence = cast("dict[str, object]", evidence["chinese"])
    chinese_evidence["eof_tail_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="deterministic evidence"):
        _validate(wrong_eof, contract, english, chinese)


def test_rejects_a_second_or_wrong_reviewer(tmp_path: Path) -> None:
    """The intake-assigned reviewer remains the sole reviewer for a source."""
    contract, english, chinese = _contract(tmp_path)
    report = _report(contract)
    report["review_model"] = "grok-4.5"

    with pytest.raises(ValueError, match="assigned reviewer"):
        _validate(report, contract, english, chinese)


def test_rejects_unknown_issue_section_and_non_unique_excerpt(
    tmp_path: Path,
) -> None:
    """Issues must bind one known section and exact unique file excerpts."""
    contract, english, chinese = _contract(tmp_path)
    issue = _semantic_issue(contract)
    issue["section_id"] = "section-9999-000000000000"
    unknown = _report(contract, verdict="fail", issues=[issue])
    with pytest.raises(ValueError, match="unknown sections"):
        _validate(unknown, contract, english, chinese)

    non_unique_issue = _semantic_issue(contract)
    non_unique_issue["source_excerpt"] = "the"
    non_unique = _report(
        contract,
        verdict="fail",
        issues=[non_unique_issue],
    )
    with pytest.raises(ValueError, match="not exact and unique"):
        _validate(non_unique, contract, english, chinese)


def test_prompt_payload_is_symmetric_and_explicit(tmp_path: Path) -> None:
    """Terra and Grok receive the same schema and three-pass instructions."""
    contract, _english, _chinese = _contract(tmp_path)
    terra = build_reviewer_contract_payload(
        contract,
        assigned_reviewer="gpt-5.6-terra",
    )
    grok = build_reviewer_contract_payload(
        contract,
        assigned_reviewer="grok-4.5",
    )
    prompt = build_reviewer_prompt(
        contract,
        assigned_reviewer="gpt-5.6-terra",
    )

    assert terra.report_schema == grok.report_schema
    assert terra.assigned_reviewer != grok.assigned_reviewer
    assert tuple(item.value for item in AuditPass) == (
        "semantic",
        "surface",
        "coverage",
    )
    assert "Pass A" in prompt
    assert "true physical EOF" in prompt
    assert "checked_section_ids" in prompt
