# Copyright 2026
# ruff: noqa: INP001, S101

"""Tests for hash-bound v3 preflight and history context."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from scripts.ai.audit_context import (
    AuditV3Context,
    build_audit_v3_context,
    build_audit_v3_slice_prompt,
    merge_audit_v3_context_reports,
)
from scripts.ai.audit_coverage import (
    AuditPass,
    CoverageIssue,
    DeepAuditCoverageContract,
    derive_coverage_contract,
)
from scripts.ai.audit_history import AuditHistoryRecovery, recover_audit_history
from scripts.ai.audit_preflight import (
    AuditPreflightEvidence,
    inspect_audit_preflight_pair,
)
from scripts.ai.audit_v3 import (
    AuditV3Slice,
    AuditV3SliceReport,
    MandatoryEvidenceDisposition,
)

if TYPE_CHECKING:
    from pathlib import Path

REVIEWER = "gpt-5.6-terra"
SOURCE_ID = "codex/audit-context-test"
LOW_CONFIDENCE_HINT_COUNT = 10
MANDATORY_HINT_LIMIT = 4


def _write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(value, encoding="utf-8", newline="\n")


def _prepared(
    tmp_path: Path,
    *,
    broken_link: bool = False,
    source_extra: str = "",
    candidate_extra: str = "",
) -> tuple[
    Path,
    Path,
    str,
    str,
    DeepAuditCoverageContract,
    AuditPreflightEvidence,
]:
    english = tmp_path / ".ai-local/audit-materialized/codex/audit-context-test/en.md"
    chinese = (
        tmp_path
        / ".ai-local/audit-materialized/codex/audit-context-test/zh-CN.md"
    )
    source = "---\ntitle: Audit\n---\n\n# Root\n\nUse safe mode.\n"
    candidate = "---\ntitle: 审核\n---\n\n# 根目录\n\n使用安全模式。\n"
    if broken_link:
        candidate += "\n[缺失章节](#missing-section)\n"
    source += source_extra
    candidate += candidate_extra
    _write(english, source)
    _write(chinese, candidate)
    contract = derive_coverage_contract(
        source_id=SOURCE_ID,
        english_path=english,
        chinese_path=chinese,
        english_path_value=english.relative_to(tmp_path).as_posix(),
        chinese_path_value=chinese.relative_to(tmp_path).as_posix(),
    )
    preflight = inspect_audit_preflight_pair(
        SOURCE_ID,
        english,
        chinese,
        source_path_value=contract.english_path,
        candidate_path_value=contract.chinese_path,
    )
    return english, chinese, source, candidate, contract, preflight


def _history(  # noqa: PLR0913
    tmp_path: Path,
    *,
    english: Path,
    chinese: Path,
    source: str,
    candidate: str,
    with_issue: bool,
) -> AuditHistoryRecovery:
    reviews = tmp_path / ".ai-local/reviews"
    if with_issue:
        report = reviews / "prior/codex/audit-context-test.json"
        report.parent.mkdir(parents=True, exist_ok=True)
        _ = report.write_text(
            json.dumps(
                {
                    "source_id": SOURCE_ID,
                    "assigned_reviewer": REVIEWER,
                    "review_model": REVIEWER,
                    "verdict": "warn",
                    "issues": [
                        {
                            "issue_id": "prior-semantic",
                            "severity": "medium",
                            "category": "semantic_conditions",
                            "location": "Root",
                            "source_excerpt": "Use safe mode.",
                            "candidate_span_text": "使用安全模式。",
                            "explanation": "The condition remains too broad.",
                        }
                    ],
                },
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return recover_audit_history(
        repo_root=tmp_path,
        source_id=SOURCE_ID,
        assigned_reviewer=REVIEWER,
        english_path=english,
        english_text=source,
        chinese_path=chinese,
        chinese_text=candidate,
        history_root=reviews,
    )


def _slice_report(
    context: AuditV3Context,
    audit_slice: AuditV3Slice,
    *,
    evidence_issue: bool,
) -> AuditV3SliceReport:
    evidence = context.mandatory_evidence[0]
    owns_evidence = evidence.evidence_id in set(
        audit_slice.mandatory_evidence_ids
    )
    section_id = next(
        item.section_id
        for item in context.plan.slices[0].coverage_units
        if item.section_id not in {"frontmatter", "preamble", "eof"}
    )
    issues = ()
    disposition = "confirmed_clean"
    issue_ids = ()
    if evidence_issue and owns_evidence:
        issue = CoverageIssue.model_validate(
            {
                "issue_id": "seeded-semantic",
                "pass": "semantic",
                "category": "semantic_conditions",
                "section_id": section_id,
                "severity": "medium",
                "location": "Root",
                "source_excerpt": "Use safe mode.",
                "candidate_span_text": "使用安全模式。",
                "explanation": "The historical condition issue remains.",
            }
        )
        issues = (issue,)
        disposition = "issue_reported"
        issue_ids = (issue.issue_id,)
    return AuditV3SliceReport.model_validate(
        {
            "version": 3,
            "plan_sha256": context.plan.plan_sha256,
            "slice_id": audit_slice.slice_id,
            "slice_sha256": audit_slice.slice_sha256,
            "coverage_contract_sha256": context.plan.coverage_contract_sha256,
            "source_id": context.source_id,
            "assigned_reviewer": REVIEWER,
            "review_model": REVIEWER,
            "source_sha256": context.source_sha256,
            "candidate_sha256": context.candidate_sha256,
            "source_eof_line": context.plan.source_eof_line,
            "candidate_eof_line": context.plan.candidate_eof_line,
            "verdict": "warn" if issues else "pass",
            "completed_units": tuple(
                item.model_dump(mode="json", by_alias=True)
                for item in audit_slice.coverage_units
            ),
            "reached_assigned_slice_end": True,
            "reached_real_eof": (
                audit_slice.role == "closure"
                or any(
                    item.section_id == "eof"
                    and item.audit_pass == AuditPass.COVERAGE
                    for item in audit_slice.coverage_units
                )
            ),
            "issue_family_sweep_completed": True,
            "issue_family_checked_issue_ids": tuple(
                issue.issue_id for issue in issues
            ),
            "mandatory_evidence_dispositions": (
                (
                    MandatoryEvidenceDisposition(
                        evidence_id=evidence.evidence_id,
                        disposition=disposition,
                        rationale="Checked against the exact current files.",
                        issue_ids=issue_ids,
                    ),
                )
                if owns_evidence
                else ()
            ),
            "issues": issues,
        }
    )


def test_builds_deterministic_context_with_preflight_and_history(
    tmp_path: Path,
) -> None:
    """Local findings and still-present history become immutable evidence."""
    english, chinese, source, candidate, contract, preflight = _prepared(
        tmp_path,
        broken_link=True,
    )
    history = _history(
        tmp_path,
        english=english,
        chinese=chinese,
        source=source,
        candidate=candidate,
        with_issue=True,
    )

    first = build_audit_v3_context(
        contract=contract,
        assigned_reviewer=REVIEWER,
        preflight=preflight,
        history=history,
    )
    second = build_audit_v3_context(
        contract=contract,
        assigned_reviewer=REVIEWER,
        preflight=preflight,
        history=history,
    )

    assert first == second
    assert first.context_sha256 == second.context_sha256
    assert {item.kind for item in first.mandatory_evidence} == {
        "preflight_hard",
        "history_carry",
    }
    requirements = {
        item.kind: item.requirement for item in first.mandatory_evidence
    }
    assert requirements == {
        "preflight_hard": "issue_required",
        "history_carry": "review_required",
    }
    assert tuple(
        item.evidence_id for item in first.mandatory_evidence
    ) == first.plan.mandatory_evidence_ids
    assert tuple(item.role for item in first.plan.slices) == (
        "semantic",
        "surface_coverage",
        "closure",
        "reconcile",
    )
    assert first.plan.slices[0].mandatory_evidence_ids == ()
    assert first.plan.slices[1].mandatory_evidence_ids == ()
    assert first.plan.slices[2].mandatory_evidence_ids == ()
    assert first.plan.slices[3].mandatory_evidence_ids == (
        first.plan.mandatory_evidence_ids
    )


def test_slice_prompt_contains_only_assigned_evidence(tmp_path: Path) -> None:
    """The prompt is hash-bound and does not invent an unplanned evidence set."""
    english, chinese, source, candidate, contract, preflight = _prepared(
        tmp_path,
        broken_link=False,
    )
    history = _history(
        tmp_path,
        english=english,
        chinese=chinese,
        source=source,
        candidate=candidate,
        with_issue=True,
    )
    context = build_audit_v3_context(
        contract=contract,
        assigned_reviewer=REVIEWER,
        preflight=preflight,
        history=history,
    )

    blind_prompt = build_audit_v3_slice_prompt(
        context,
        context.plan.slices[0],
        contract=contract,
    )
    evidence_prompt = build_audit_v3_slice_prompt(
        context,
        context.plan.slices[3],
        contract=contract,
    )
    closure_prompt = build_audit_v3_slice_prompt(
        context,
        context.plan.slices[2],
        contract=contract,
    )

    assert context.context_sha256 in blind_prompt
    assert context.plan.plan_sha256 in blind_prompt
    assert context.mandatory_evidence[0].evidence_id not in blind_prompt
    assert context.mandatory_evidence[0].evidence_id in evidence_prompt
    assert "issue_required evidence must be issue_reported" in evidence_prompt
    assert "reconcile slice has no primary coverage units" in evidence_prompt
    assert "adversarial closure slice" in closure_prompt
    assert "text, markdown, md, or plaintext" in closure_prompt
    assert "must not be reported as residual English" in closure_prompt
    assert "Executable-language fences are immutable" in closure_prompt
    assert "never include the opening or closing fence marker" in closure_prompt
    assert "dangling sentence-final words" in closure_prompt
    assert '"complexity_metrics": {' in closure_prompt
    assert "compare every card's title, label, date, and description" in blind_prompt
    assert "Start with a blind second semantic pass" in closure_prompt


def test_context_caps_low_confidence_preflight_hints(tmp_path: Path) -> None:
    """Low-confidence hints are ranked and bounded before reaching a reviewer."""
    links = "".join(
        f"\n[English guide {index}](/guide/{index})\n"
        for index in range(LOW_CONFIDENCE_HINT_COUNT)
    )
    english, chinese, source, candidate, contract, preflight = _prepared(
        tmp_path,
        source_extra=links,
        candidate_extra=links,
    )
    history = _history(
        tmp_path,
        english=english,
        chinese=chinese,
        source=source,
        candidate=candidate,
        with_issue=False,
    )

    context = build_audit_v3_context(
        contract=contract,
        assigned_reviewer=REVIEWER,
        preflight=preflight,
        history=history,
    )

    assert len(preflight.findings) == LOW_CONFIDENCE_HINT_COUNT
    hints = [
        item
        for item in context.mandatory_evidence
        if item.kind == "preflight_hint"
    ]
    assert len(hints) == MANDATORY_HINT_LIMIT
    ordered = sorted(preflight.findings, key=lambda item: item.candidate_lines)
    selected_ids = {item.origin_ids[0] for item in hints}
    assert ordered[0].finding_id in selected_ids
    assert ordered[-1].finding_id in selected_ids


def test_context_preserves_exact_preflight_span_bytes(tmp_path: Path) -> None:
    """Mandatory evidence retains the exact bytes used by span hashing."""
    english, chinese, source, candidate, contract, preflight = _prepared(
        tmp_path,
        source_extra="\n## Setup\n",
        candidate_extra="\n  ### 设置   \n",
    )
    history = _history(
        tmp_path,
        english=english,
        chinese=chinese,
        source=source,
        candidate=candidate,
        with_issue=False,
    )

    context = build_audit_v3_context(
        contract=contract,
        assigned_reviewer=REVIEWER,
        preflight=preflight,
        history=history,
    )

    evidence = next(
        item
        for item in context.mandatory_evidence
        if item.kind == "preflight_hard"
    )
    assert evidence.candidate_span_text == "  ### 设置   "


def test_history_carry_requires_reasoned_recheck_not_forced_issue(
    tmp_path: Path,
) -> None:
    """Current history remains review evidence rather than an immutable verdict."""
    english, chinese, source, candidate, contract, preflight = _prepared(
        tmp_path,
        broken_link=False,
    )
    history = _history(
        tmp_path,
        english=english,
        chinese=chinese,
        source=source,
        candidate=candidate,
        with_issue=True,
    )
    context = build_audit_v3_context(
        contract=contract,
        assigned_reviewer=REVIEWER,
        preflight=preflight,
        history=history,
    )
    audit_slices = context.plan.slices

    clean = merge_audit_v3_context_reports(
        context=context,
        reports=tuple(
            _slice_report(
                context,
                audit_slice,
                evidence_issue=False,
            )
            for audit_slice in audit_slices
        ),
        contract=contract,
    )
    assert clean.verdict == "pass"

    merged = merge_audit_v3_context_reports(
        context=context,
        reports=tuple(
            _slice_report(
                context,
                audit_slice,
                evidence_issue=True,
            )
            for audit_slice in audit_slices
        ),
        contract=contract,
    )
    assert merged.verdict == "warn"
    assert merged.issues[0].issue_id == "seeded-semantic"
