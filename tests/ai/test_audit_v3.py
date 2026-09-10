# Copyright 2026
# ruff: noqa: INP001, S101

"""Tests for orthogonal v3 deep-audit planning and fail-closed merging."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import TYPE_CHECKING, cast

import pytest
from pydantic import ValidationError

from scripts.ai.audit_coverage import (
    AuditPass,
    CoverageIssue,
    DeepAuditCoverageContract,
    derive_coverage_contract,
)
from scripts.ai.audit_v3 import (
    AuditV3Plan,
    AuditV3Slice,
    AuditV3SliceReport,
    MandatoryEvidenceDisposition,
    build_audit_v3_plan,
    merge_audit_v3_reports,
    validate_audit_v3_plan,
)

if TYPE_CHECKING:
    from pathlib import Path

REVIEWER = "gpt-5.6-terra"
H2_LEVEL = 2
MIN_SEMANTIC_GROUPS = 2
MAX_SEMANTIC_GROUPS = 4


def _write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(value, encoding="utf-8", newline="\n")


def _markdown(
    headings: list[tuple[int, str]],
    *,
    extra_lines: int = 0,
    dense_bytes: int = 0,
) -> str:
    parts = ["---", "title: Audit", "---", "Preamble."]
    for index, (level, heading) in enumerate(headings):
        parts.extend(("#" * level + f" {heading}", f"Body {index}."))
    parts.extend(f"Padding {index}." for index in range(extra_lines))
    if dense_bytes:
        parts.append("X" * dense_bytes)
    return "\n\n".join(parts) + "\n"


def _contract(
    tmp_path: Path,
    *,
    headings: list[tuple[int, str]],
    extra_lines: int = 0,
    dense_bytes: int = 0,
) -> DeepAuditCoverageContract:
    english = tmp_path / "materialized/en.md"
    chinese = tmp_path / "materialized/zh-CN.md"
    _write(
        english,
        _markdown(
            headings,
            extra_lines=extra_lines,
            dense_bytes=dense_bytes,
        ),
    )
    _write(
        chinese,
        _markdown(
            [(level, f"中文-{heading}") for level, heading in headings],
            extra_lines=extra_lines,
            dense_bytes=dense_bytes,
        ),
    )
    return derive_coverage_contract(
        source_id="codex/audit-v3-test",
        english_path=english,
        chinese_path=chinese,
        english_path_value="materialized/en.md",
        chinese_path_value="materialized/zh-CN.md",
    )


def _report(  # noqa: PLR0913
    plan: AuditV3Plan,
    audit_slice: AuditV3Slice,
    *,
    issues: tuple[CoverageIssue, ...] = (),
    completed_units: tuple[object, ...] | None = None,
    reviewer: str = REVIEWER,
    dispositions: tuple[MandatoryEvidenceDisposition, ...] | None = None,
) -> AuditV3SliceReport:
    if dispositions is None:
        dispositions = tuple(
            MandatoryEvidenceDisposition(
                evidence_id=evidence_id,
                disposition="confirmed_clean",
                rationale="Checked against the exact final-shape files.",
            )
            for evidence_id in audit_slice.mandatory_evidence_ids
        )
    verdict = (
        "fail"
        if any(issue.severity == "high" for issue in issues)
        else "warn"
        if issues
        else "pass"
    )
    return AuditV3SliceReport.model_validate(
        {
            "version": 3,
            "plan_sha256": plan.plan_sha256,
            "slice_id": audit_slice.slice_id,
            "slice_sha256": audit_slice.slice_sha256,
            "coverage_contract_sha256": plan.coverage_contract_sha256,
            "source_id": plan.source_id,
            "assigned_reviewer": reviewer,
            "review_model": reviewer,
            "source_sha256": plan.source_sha256,
            "candidate_sha256": plan.candidate_sha256,
            "source_eof_line": plan.source_eof_line,
            "candidate_eof_line": plan.candidate_eof_line,
            "verdict": verdict,
            "completed_units": (
                completed_units
                if completed_units is not None
                else audit_slice.coverage_units
            ),
            "reached_assigned_slice_end": True,
            "reached_real_eof": (
                audit_slice.role == "closure"
                or any(
                    unit.section_id == "eof"
                    and AuditPass(unit.audit_pass) == AuditPass.COVERAGE
                    for unit in audit_slice.coverage_units
                )
            ),
            "issue_family_sweep_completed": True,
            "issue_family_checked_issue_ids": tuple(
                issue.issue_id for issue in issues
            ),
            "mandatory_evidence_dispositions": dispositions,
            "issues": issues,
        }
    )


def _reports(plan: AuditV3Plan) -> tuple[AuditV3SliceReport, ...]:
    return tuple(_report(plan, audit_slice) for audit_slice in plan.slices)


def test_slice_report_rejects_incomplete_issue_family_closure(
    tmp_path: Path,
) -> None:
    """Every reported issue must be covered by the explicit family sweep."""
    contract = _contract(tmp_path, headings=[(1, "Root"), (2, "Details")])
    plan = build_audit_v3_plan(contract=contract, assigned_reviewer=REVIEWER)
    issue = CoverageIssue.model_validate(
        {
            "issue_id": "semantic-family-1",
            "pass": "semantic",
            "category": "semantic_roles",
            "section_id": next(
                item.section_id
                for item in contract.sections
                if item.kind == "heading"
            ),
            "severity": "medium",
            "location": "Root",
            "source_excerpt": "Body 0.",
            "candidate_span_text": "Body 0.",
            "explanation": "The actor is reversed.",
        }
    )
    payload = _report(
        plan,
        plan.slices[0],
        issues=(issue,),
    ).model_dump(mode="json", by_alias=True)
    payload["issue_family_checked_issue_ids"] = []

    with pytest.raises(ValidationError, match="issue-family closure"):
        _ = AuditV3SliceReport.model_validate(payload)


@pytest.mark.parametrize(
    ("headings", "extra_lines", "expected", "roles"),
    [
        (
            [(1, "Root"), (2, "Details")],
            0,
            "simple",
            ("abc",),
        ),
        (
            [(1, "Root"), *[(2, f"Part {index}") for index in range(40)]],
            0,
            "complex",
            ("semantic", "surface_coverage"),
        ),
        (
            [(1, "Root"), *[(2, f"Part {index}") for index in range(48)]],
            0,
            "extreme",
            None,
        ),
    ],
)
def test_builds_three_complexity_classes(
    tmp_path: Path,
    headings: list[tuple[int, str]],
    extra_lines: int,
    expected: str,
    roles: tuple[str, ...] | None,
) -> None:
    """Thresholds produce the required orthogonal topology for each class."""
    contract = _contract(
        tmp_path,
        headings=headings,
        extra_lines=extra_lines,
    )

    plan = build_audit_v3_plan(contract=contract, assigned_reviewer=REVIEWER)

    assert plan.complexity == expected
    if roles is not None:
        assert tuple(item.role for item in plan.slices) == roles
    else:
        semantic = [item for item in plan.slices if item.role == "semantic"]
        assert MIN_SEMANTIC_GROUPS <= len(semantic) <= MAX_SEMANTIC_GROUPS
        assert tuple(item.role for item in plan.slices[-2:]) == (
            "surface",
            "coverage",
        )


def test_adversarial_closure_is_independent_and_may_find_any_page_issue(
    tmp_path: Path,
) -> None:
    """The independent closure may report missed issues from any pass."""
    contract = _contract(
        tmp_path,
        headings=[(1, "Root"), (2, "Details")],
    )
    plan = build_audit_v3_plan(
        contract=contract,
        assigned_reviewer=REVIEWER,
        orthogonal_simple=True,
        adversarial_closure=True,
    )
    closure = plan.slices[-1]
    section_id = next(
        item.section_id for item in contract.sections if item.kind == "heading"
    )
    issue = CoverageIssue.model_validate(
        {
            "issue_id": "closure-dangling-fragment",
            "pass": "semantic",
            "category": "semantic_roles",
            "section_id": section_id,
            "severity": "medium",
            "location": "Details",
            "source_excerpt": "The session resumes in the launch directory.",
            "candidate_span_text": "会话会在启动目录中恢复 从。",
            "explanation": "A dangling final word makes the conclusion incomplete.",
        }
    )
    reports = tuple(
        _report(plan, audit_slice, issues=(issue,) if audit_slice == closure else ())
        for audit_slice in plan.slices
    )

    merged = merge_audit_v3_reports(
        plan=plan,
        reports=reports,
        contract=contract,
    )

    assert tuple(item.role for item in plan.slices) == (
        "semantic",
        "surface_coverage",
        "closure",
    )
    assert closure.coverage_units == ()
    assert merged.verdict == "warn"
    assert [item.issue_id for item in merged.issues] == [
        "closure-dangling-fragment"
    ]


def test_adversarial_closure_must_read_the_real_eof(tmp_path: Path) -> None:
    """A closure report cannot claim completion after a truncated read."""
    contract = _contract(
        tmp_path,
        headings=[(1, "Root"), (2, "Details")],
    )
    plan = build_audit_v3_plan(
        contract=contract,
        assigned_reviewer=REVIEWER,
        orthogonal_simple=True,
        adversarial_closure=True,
    )
    reports = list(_reports(plan))
    payload = reports[-1].model_dump(mode="json", by_alias=True)
    payload["reached_real_eof"] = False
    reports[-1] = AuditV3SliceReport.model_validate(payload)

    with pytest.raises(ValueError, match="full-page read"):
        _ = merge_audit_v3_reports(
            plan=plan,
            reports=tuple(reports),
            contract=contract,
        )


def test_extreme_semantic_slices_keep_h2_subtrees_intact(
    tmp_path: Path,
) -> None:
    """An H2 and all following H3 descendants always share one semantic slice."""
    headings = [(1, "Root")]
    for index in range(27):
        headings.extend(
            (
                (2, f"Chapter {index}"),
                (3, f"Chapter {index} A"),
                (3, f"Chapter {index} B"),
            )
        )
    contract = _contract(tmp_path, headings=headings)
    plan = build_audit_v3_plan(contract=contract, assigned_reviewer=REVIEWER)
    semantic_owner = {
        section_id: audit_slice.slice_id
        for audit_slice in plan.slices
        if audit_slice.role == "semantic"
        for section_id in audit_slice.section_ids
    }
    sections = list(contract.sections)

    for index, section in enumerate(sections):
        if section.english_level != H2_LEVEL:
            continue
        subtree = [section.section_id]
        for descendant in sections[index + 1 :]:
            level = descendant.english_level
            if (
                descendant.kind == "heading"
                and level is not None
                and level <= H2_LEVEL
            ):
                break
            subtree.append(descendant.section_id)
        assert len({semantic_owner[item] for item in subtree}) == 1


@pytest.mark.parametrize(
    ("dense_bytes", "expected", "roles"),
    [
        (19_000, "simple", ("abc",)),
        (25_000, "complex", ("semantic", "surface_coverage")),
        (65_000, "extreme", None),
    ],
)
def test_byte_dense_pages_receive_stronger_audit_topologies(
    tmp_path: Path,
    dense_bytes: int,
    expected: str,
    roles: tuple[str, ...] | None,
) -> None:
    """Physical line count cannot hide large, attention-heavy pages."""
    contract = _contract(
        tmp_path,
        headings=[(1, "Root"), (2, "First"), (2, "Second")],
        dense_bytes=dense_bytes,
    )

    plan = build_audit_v3_plan(contract=contract, assigned_reviewer=REVIEWER)

    assert plan.complexity == expected
    assert plan.complexity_metrics.byte_count == max(
        contract.evidence.english.byte_count,
        contract.evidence.chinese.byte_count,
    )
    if roles is not None:
        assert tuple(item.role for item in plan.slices) == roles
    else:
        semantic = [item for item in plan.slices if item.role == "semantic"]
        assert MIN_SEMANTIC_GROUPS <= len(semantic) <= MAX_SEMANTIC_GROUPS
        assert tuple(item.role for item in plan.slices[-2:]) == (
            "surface",
            "coverage",
        )


def test_legacy_plan_hash_without_byte_count_remains_valid(
    tmp_path: Path,
) -> None:
    """Stored v3 plans remain resumable after byte-aware classification ships."""
    contract = _contract(tmp_path, headings=[(1, "Root"), (2, "Details")])
    current = build_audit_v3_plan(
        contract=contract,
        assigned_reviewer=REVIEWER,
    )
    legacy = current.model_dump(mode="json", by_alias=True)
    metrics = cast("dict[str, object]", legacy["complexity_metrics"])
    _ = metrics.pop("byte_count")
    hash_payload = deepcopy(legacy)
    _ = hash_payload.pop("plan_sha256")
    encoded = json.dumps(
        hash_payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    legacy["plan_sha256"] = hashlib.sha256(encoded).hexdigest()

    restored = AuditV3Plan.model_validate(legacy)
    validate_audit_v3_plan(restored, contract=contract)

    assert restored.complexity_metrics.byte_count is None
    assert restored.plan_sha256 == legacy["plan_sha256"]


def test_merge_rejects_missing_slice_and_wrong_reviewer(
    tmp_path: Path,
) -> None:
    """Every planned slice must report once under the sole assigned reviewer."""
    contract = _contract(
        tmp_path,
        headings=[(1, "Root"), *[(2, f"Part {index}") for index in range(40)]],
    )
    plan = build_audit_v3_plan(contract=contract, assigned_reviewer=REVIEWER)
    reports = _reports(plan)

    with pytest.raises(ValueError, match="missing"):
        _ = merge_audit_v3_reports(
            plan=plan,
            reports=reports[:-1],
            contract=contract,
        )

    wrong = _report(plan, plan.slices[0], reviewer="grok-4.5")
    with pytest.raises(ValueError, match="assigned reviewer"):
        _ = merge_audit_v3_reports(
            plan=plan,
            reports=(wrong, reports[1]),
            contract=contract,
        )


def test_merge_rejects_missing_actual_coverage(
    tmp_path: Path,
) -> None:
    """A slice cannot claim a copied full-page ledger after omitting one unit."""
    contract = _contract(
        tmp_path,
        headings=[(1, "Root"), *[(2, f"Part {index}") for index in range(40)]],
    )
    plan = build_audit_v3_plan(contract=contract, assigned_reviewer=REVIEWER)
    first = plan.slices[0]
    incomplete = _report(
        plan,
        first,
        completed_units=cast("tuple[object, ...]", first.coverage_units[:-1]),
    )

    with pytest.raises(ValueError, match="did not complete its actual units"):
        _ = merge_audit_v3_reports(
            plan=plan,
            reports=(incomplete, _report(plan, plan.slices[1])),
            contract=contract,
        )


def test_merge_conserves_conflicting_findings_for_one_exact_candidate_span(
    tmp_path: Path,
) -> None:
    """Orthogonal findings become one repair-safe span without losing reasons."""
    contract = _contract(
        tmp_path,
        headings=[(1, "Root"), *[(2, f"Part {index}") for index in range(40)]],
    )
    plan = build_audit_v3_plan(contract=contract, assigned_reviewer=REVIEWER)
    section_id = next(
        item.section_id for item in contract.sections if item.kind == "heading"
    )
    semantic = CoverageIssue.model_validate(
        {
            "issue_id": "semantic-1",
            "pass": "semantic",
            "category": "semantic_roles",
            "section_id": section_id,
            "severity": "medium",
            "location": "Root",
            "source_excerpt": "Body 0.",
            "candidate_span_text": "Body 0.",
            "explanation": "Semantic role mismatch.",
        }
    )
    surface = CoverageIssue.model_validate(
        {
            "issue_id": "surface-1",
            "pass": "surface",
            "category": "surface_terminology",
            "section_id": section_id,
            "severity": "low",
            "location": "Root",
            "source_excerpt": "Body 0.",
            "candidate_span_text": "Body 0.",
            "explanation": "Terminology mismatch.",
        }
    )

    merged = merge_audit_v3_reports(
        plan=plan,
        reports=(
            _report(plan, plan.slices[0], issues=(semantic,)),
            _report(plan, plan.slices[1], issues=(surface,)),
        ),
        contract=contract,
    )

    assert len(merged.issues) == 1
    issue = merged.issues[0]
    assert issue.issue_id == semantic.issue_id
    assert issue.audit_pass == semantic.audit_pass
    assert issue.severity == "medium"
    assert issue.candidate_span_text == "Body 0."
    assert "Semantic role mismatch." in issue.explanation
    assert "Terminology mismatch." in issue.explanation


def test_merge_rejects_unclosed_mandatory_evidence(
    tmp_path: Path,
) -> None:
    """Historical seeds and preflight facts must close before a clean pass."""
    contract = _contract(tmp_path, headings=[(1, "Root"), (2, "Details")])
    plan = build_audit_v3_plan(
        contract=contract,
        assigned_reviewer=REVIEWER,
        mandatory_evidence_ids=("history:old-warning",),
    )
    unresolved = (
        MandatoryEvidenceDisposition(
            evidence_id="history:old-warning",
            disposition="unresolved",
            rationale="The reviewer did not inspect the historical warning.",
        ),
    )
    reports = list(_reports(plan))
    evidence_slice = plan.slices[-1]
    reports[-1] = _report(
        plan,
        evidence_slice,
        dispositions=unresolved,
    )

    with pytest.raises(ValueError, match="remains unresolved"):
        _ = merge_audit_v3_reports(
            plan=plan,
            reports=tuple(reports),
            contract=contract,
        )


def test_mandatory_evidence_may_report_issue_outside_primary_slice_units(
    tmp_path: Path,
) -> None:
    """Evidence reconciliation may add a finding without claiming its audit unit."""
    contract = _contract(
        tmp_path,
        headings=[(1, "Root"), *[(2, f"Part {index}") for index in range(40)]],
    )
    plan = build_audit_v3_plan(
        contract=contract,
        assigned_reviewer=REVIEWER,
        mandatory_evidence_ids=("history:semantic-condition",),
    )
    section_id = next(
        item.section_id for item in contract.sections if item.kind == "heading"
    )
    issue = CoverageIssue.model_validate(
        {
            "issue_id": "history-semantic-1",
            "pass": "semantic",
            "category": "semantic_conditions",
            "section_id": section_id,
            "severity": "medium",
            "location": "Root",
            "source_excerpt": "Body 0.",
            "candidate_span_text": "Body 0.",
            "explanation": "Historical evidence still exposes a condition mismatch.",
        }
    )
    evidence_slice = plan.slices[-1]
    dispositions = (
        MandatoryEvidenceDisposition(
            evidence_id="history:semantic-condition",
            disposition="issue_reported",
            rationale="The exact historical span remains incorrect.",
            issue_ids=(issue.issue_id,),
        ),
    )

    merged = merge_audit_v3_reports(
        plan=plan,
        reports=(
            *(_report(plan, item) for item in plan.slices[:-1]),
            _report(
                plan,
                evidence_slice,
                issues=(issue,),
                dispositions=dispositions,
            ),
        ),
        contract=contract,
    )

    assert merged.issues == (issue,)
    assert evidence_slice.coverage_units == ()


def test_out_of_slice_issue_without_evidence_reference_is_rejected(
    tmp_path: Path,
) -> None:
    """A slice cannot use evidence reconciliation as a general scope escape."""
    contract = _contract(
        tmp_path,
        headings=[(1, "Root"), *[(2, f"Part {index}") for index in range(40)]],
    )
    plan = build_audit_v3_plan(
        contract=contract,
        assigned_reviewer=REVIEWER,
        mandatory_evidence_ids=("history:semantic-condition",),
    )
    section_id = next(
        item.section_id for item in contract.sections if item.kind == "heading"
    )
    issue = CoverageIssue.model_validate(
        {
            "issue_id": "unrelated-semantic-1",
            "pass": "semantic",
            "category": "semantic_conditions",
            "section_id": section_id,
            "severity": "medium",
            "location": "Root",
            "source_excerpt": "Body 0.",
            "candidate_span_text": "Body 0.",
            "explanation": "This issue is not tied to the mandatory evidence.",
        }
    )
    evidence_slice = plan.slices[-1]
    reports = (
        *(_report(plan, item) for item in plan.slices[:-1]),
        _report(plan, evidence_slice, issues=(issue,)),
    )

    with pytest.raises(ValueError, match="outside slice"):
        _ = merge_audit_v3_reports(
            plan=plan,
            reports=reports,
            contract=contract,
        )


def test_legal_merge_outputs_standard_finding_report(
    tmp_path: Path,
) -> None:
    """A complete orthogonal run merges into the existing bridge schema."""
    contract = _contract(
        tmp_path,
        headings=[(1, "Root"), *[(2, f"Part {index}") for index in range(40)]],
    )
    plan = build_audit_v3_plan(
        contract=contract,
        assigned_reviewer=REVIEWER,
        mandatory_evidence_ids=("preflight:links",),
    )
    section_id = next(
        item.section_id for item in contract.sections if item.kind == "heading"
    )
    issue = CoverageIssue.model_validate(
        {
            "issue_id": "semantic-1",
            "pass": "semantic",
            "category": "semantic_conditions",
            "section_id": section_id,
            "severity": "medium",
            "location": "Root",
            "source_excerpt": "Body 0.",
            "candidate_span_text": "Body 0.",
            "explanation": "The condition is too broad.",
        }
    )
    reports = tuple(
        _report(
            plan,
            audit_slice,
            issues=(issue,) if index == 0 else (),
        )
        for index, audit_slice in enumerate(plan.slices)
    )

    merged = merge_audit_v3_reports(
        plan=plan,
        reports=reports,
        contract=contract,
    )

    assert merged.verdict == "warn"
    assert merged.review_model == REVIEWER
    assert merged.issues == (issue,)
    assert merged.checked_section_ids == tuple(
        item.section_id for item in contract.sections
    )
    assert merged.reached_real_eof is True


def test_hash_bound_plan_rejects_mutation(tmp_path: Path) -> None:
    """A plan or slice cannot be edited without recomputing its identity."""
    contract = _contract(tmp_path, headings=[(1, "Root"), (2, "Details")])
    plan = build_audit_v3_plan(contract=contract, assigned_reviewer=REVIEWER)
    value = plan.model_dump(mode="json", by_alias=True)
    value["candidate_sha256"] = "0" * 64

    with pytest.raises(ValidationError, match="hash"):
        _ = AuditV3Plan.model_validate(value)

    slice_value = deepcopy(plan.slices[0].model_dump(mode="json", by_alias=True))
    slice_value["source_eof_line"] = cast("int", slice_value["source_eof_line"]) + 1
    with pytest.raises(ValidationError, match="hash"):
        _ = AuditV3Slice.model_validate(slice_value)
