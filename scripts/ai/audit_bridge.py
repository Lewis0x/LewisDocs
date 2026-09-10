# Copyright 2026

"""Strict adapters from deep-audit reports to repair-ready pipeline inputs."""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, ClassVar, Literal, Self, cast

from pydantic import BaseModel, ConfigDict, Field, model_validator

from scripts.ai.audit_coverage import (
    DeepAuditCoverageContract,
    recover_unique_whitespace_span,
    validate_coverage_contract,
    validate_coverage_report,
)
from scripts.ai.pipeline import Provider, ProviderModel, RepairJob, RepairJobSpec
from scripts.ai.pipeline_adapters import review_structure_counts
from scripts.ai.review_contract import (
    AssignedReviewer,
    RepairIssueDraft,
    RepairReadyReview,
    RepairReadyReviewDraft,
    materialize_repair_ready_review,
    resolve_repo_path,
    sha256_path,
    write_repair_ready_review,
)

if TYPE_CHECKING:
    from pathlib import Path

    from scripts.ai.pipeline import PipelineStore

_SAME_PAGE_LINK_TARGET = re.compile(r"\]\(#[^)]+\)")
_MARKDOWN_LINK = re.compile(r"\[([^\]\n]+)\]\(([^)\n]+)\)")
_PUBLIC_ENGLISH_TITLE_PREFIX = "title: EN · "
_PUBLIC_CHINESE_TITLE_PREFIX = "title: 中文 · "
_MIN_HASH_BINDINGS = 2
_MIN_EOF_LANGUAGE_RECORDS = 2
_COVERAGE_CONTRACT_VERSION = 2
_REVIEW_WORKFLOW_V3 = 3
TranslationModel = Literal["k3", "glm-5.2", "gpt-5.6"]


class _StrictModel(BaseModel):
    """Immutable deep-audit bridge record base."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )


class DeepAuditManifestEntry(_StrictModel):
    """One prepared final-site-shape pair awaiting a single assigned reviewer."""

    audit_contract_version: Literal[1, 2] = 1
    review_workflow_version: Literal[2, 3] = 2
    source_id: str = Field(min_length=1)
    status: Literal["prepared"]
    english_path: str = Field(min_length=1)
    chinese_path: str = Field(min_length=1)
    normalized_candidate_path: str = Field(min_length=1)
    producer: str = Field(min_length=1)
    translation_model: TranslationModel
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    candidate_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    normalized_candidate_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    fenced_blocks_restored: int = Field(default=0, ge=0)
    source_shard: int | None = Field(default=None, ge=0)
    source_entry_index: int | None = Field(default=None, ge=0)
    coverage_contract: DeepAuditCoverageContract | None = None
    preflight_path: str | None = None
    preflight_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    history_path: str | None = None
    history_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    v3_context_path: str | None = None
    v3_context_sha256: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )
    v3_plan_path: str | None = None
    v3_plan_sha256: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )

    @model_validator(mode="after")
    def _v2_has_coverage_contract(self) -> Self:
        if (
            self.audit_contract_version == _COVERAGE_CONTRACT_VERSION
            and self.coverage_contract is None
        ):
            message = "v2 deep-audit manifest entry has no coverage contract"
            raise ValueError(message)
        v3_artifacts = (
            self.preflight_path,
            self.preflight_sha256,
            self.history_path,
            self.history_sha256,
            self.v3_context_path,
            self.v3_context_sha256,
            self.v3_plan_path,
            self.v3_plan_sha256,
        )
        if self.review_workflow_version == _REVIEW_WORKFLOW_V3 and any(
            value is None for value in v3_artifacts
        ):
            message = "v3 deep-audit manifest entry lacks evidence artifacts"
            raise ValueError(message)
        return self


class DeepAuditManifest(_StrictModel):
    """Prepared deep-audit inputs, including explicitly blocked entries."""

    version: Literal[1] = 1
    purpose: str = Field(min_length=1)
    entries: tuple[dict[str, object], ...] = Field(min_length=1)


class DeepAuditBridgeResult(_StrictModel):
    """One verified audit report and its queued repair job."""

    version: Literal[1] = 1
    source_id: str
    assigned_reviewer: AssignedReviewer
    provider: Provider
    report_path: str
    repair_review_path: str
    repair_review_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    job: RepairJob


class ValidatedDeepAuditReport(_StrictModel):
    """Hash-bound result of one complete assigned deep audit."""

    version: Literal[1] = 1
    source_id: str
    assigned_reviewer: AssignedReviewer
    verdict: Literal["pass", "warn", "fail"]
    report_path: str
    report_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


def bridge_deep_audit_report(
    *,
    repo_root: Path,
    manifest_path: Path,
    report_path: Path,
    source_id: str,
    assigned_reviewer: AssignedReviewer,
) -> RepairReadyReview:
    """Validate one complete deep audit and derive exact repair spans."""
    entry = _load_entry(manifest_path, source_id)
    _validate_entry_files(repo_root, entry)
    validated = validate_deep_audit_report(
        repo_root=repo_root,
        manifest_path=manifest_path,
        report_path=report_path,
        source_id=source_id,
        assigned_reviewer=assigned_reviewer,
    )
    report = cast(
        "dict[str, object]",
        json.loads(report_path.read_text(encoding="utf-8-sig")),
    )
    verdict = validated.verdict
    if verdict == "pass":
        message = "clean deep audits require the audited-adoption path"
        raise ValueError(message)

    raw_source_path = (
        repo_root / "source-ai" / "content" / "en" / f"{source_id}.md"
    )
    if not raw_source_path.is_file():
        message = f"raw English source is missing: {source_id}"
        raise ValueError(message)
    raw_candidate_path = resolve_repo_path(
        repo_root,
        entry.normalized_candidate_path,
    )
    raw_source = raw_source_path.read_text(encoding="utf-8-sig")
    raw_candidate = raw_candidate_path.read_text(encoding="utf-8-sig")
    issues_value = report.get("issues")
    if not isinstance(issues_value, list) or not issues_value:
        message = "non-passing deep audit has no issues"
        raise ValueError(message)
    issue_values = cast("list[object]", issues_value)
    issues = tuple(
        _repair_issue_draft(
            issue,
            index=index,
            raw_source=raw_source,
            raw_candidate=raw_candidate,
            assigned_reviewer=assigned_reviewer,
        )
        for index, issue in enumerate(issue_values)
    )
    issues = _coalesce_overlapping_repair_drafts(
        issues,
        raw_candidate=raw_candidate,
    )
    report_value = _repo_relative(report_path, repo_root)
    draft = RepairReadyReviewDraft(
        version=2,
        source_id=source_id,
        assigned_reviewer=assigned_reviewer,
        verdict=verdict,
        source_path=_repo_relative(raw_source_path, repo_root),
        candidate_path=entry.normalized_candidate_path,
        source_report_paths=(report_value,),
        issues=issues,
    )
    return materialize_repair_ready_review(draft, repo_root)


def _coalesce_overlapping_repair_drafts(
    issues: tuple[RepairIssueDraft, ...],
    *,
    raw_candidate: str,
) -> tuple[RepairIssueDraft, ...]:
    """Merge connected repair ranges before a provider sees span ids."""
    positioned: list[tuple[int, int, RepairIssueDraft]] = []
    for issue in issues:
        count = raw_candidate.count(issue.candidate_span_text)
        if count != 1:
            message = (
                "deep-audit repair span is not unique before overlap "
                f"coalescing: {count} matches"
            )
            raise ValueError(message)
        start = raw_candidate.index(issue.candidate_span_text)
        positioned.append(
            (start, start + len(issue.candidate_span_text), issue)
        )
    positioned.sort(key=lambda value: (value[0], value[1]))

    groups: list[list[tuple[int, int, RepairIssueDraft]]] = []
    for value in positioned:
        if not groups or value[0] >= max(item[1] for item in groups[-1]):
            groups.append([value])
        else:
            groups[-1].append(value)
    return tuple(
        _merge_repair_range(group, raw_candidate=raw_candidate)
        for group in groups
    )


def _merge_repair_range(
    group: list[tuple[int, int, RepairIssueDraft]],
    *,
    raw_candidate: str,
) -> RepairIssueDraft:
    """Conserve every finding inside one indivisible replacement range."""
    if len(group) == 1:
        return group[0][2]
    severity_order = {"high": 0, "medium": 1, "low": 2}
    canonical = min(
        (item[2] for item in group),
        key=lambda issue: (
            severity_order[issue.severity],
            issue.category,
            issue.location,
            issue.candidate_span_text,
        ),
    )
    start = min(item[0] for item in group)
    end = max(item[1] for item in group)
    explanations = tuple(
        dict.fromkeys(
            (
                f"[{','.join(issue.source_issue_refs)}] "
                f"Source: {issue.source_excerpt} Finding: {issue.explanation}"
            )
            for _, _, issue in group
        )
    )
    return RepairIssueDraft(
        source_issue_refs=tuple(
            sorted(
                {
                    reference
                    for _, _, issue in group
                    for reference in issue.source_issue_refs
                }
            )
        ),
        severity=canonical.severity,
        category=canonical.category,
        location=canonical.location,
        source_excerpt=canonical.source_excerpt,
        candidate_span_text=raw_candidate[start:end],
        explanation="\n".join(explanations),
    )


def validate_deep_audit_report(
    *,
    repo_root: Path,
    manifest_path: Path,
    report_path: Path,
    source_id: str,
    assigned_reviewer: AssignedReviewer,
) -> ValidatedDeepAuditReport:
    """Validate report ownership, hashes, structure, issues, and real EOF."""
    entry = _load_entry(manifest_path, source_id)
    _validate_entry_files(repo_root, entry)
    report = cast(
        "dict[str, object]",
        json.loads(report_path.read_text(encoding="utf-8-sig")),
    )
    verdict = _validate_report(
        repo_root=repo_root,
        report=report,
        report_path=report_path,
        entry=entry,
        assigned_reviewer=assigned_reviewer,
    )
    return ValidatedDeepAuditReport(
        source_id=source_id,
        assigned_reviewer=assigned_reviewer,
        verdict=verdict,
        report_path=_repo_relative(report_path, repo_root),
        report_sha256=sha256_path(report_path),
    )


def bridge_and_queue_deep_audit(  # noqa: PLR0913
    *,
    store: PipelineStore,
    manifest_path: Path,
    report_path: Path,
    repair_review_path: Path,
    source_id: str,
    assigned_reviewer: AssignedReviewer,
    provider: Provider,
    attempt_id: str,
    actor: str,
    intake_id: str | None = None,
) -> DeepAuditBridgeResult:
    """Bridge one report, write immutable evidence, and queue its repair."""
    review = bridge_deep_audit_report(
        repo_root=store.repo_root,
        manifest_path=manifest_path,
        report_path=report_path,
        source_id=source_id,
        assigned_reviewer=assigned_reviewer,
    )
    write_repair_ready_review(repair_review_path, review)
    model: ProviderModel = "k3" if provider == "kimi" else "glm-5.2"
    spec = RepairJobSpec(
        source_id=review.source_id,
        source_path=review.source_path,
        candidate_path=review.candidate_path,
        source_sha256=review.source_sha256,
        base_candidate_sha256=review.candidate_sha256,
        review_path=_repo_relative(repair_review_path, store.repo_root),
        assigned_reviewer=review.assigned_reviewer,
        provider=provider,
        provider_model=model,
        attempt_id=attempt_id,
        intake_id=intake_id,
    )
    job = store.create_job(spec, actor=actor)
    return DeepAuditBridgeResult(
        source_id=source_id,
        assigned_reviewer=assigned_reviewer,
        provider=provider,
        report_path=_repo_relative(report_path, store.repo_root),
        repair_review_path=_repo_relative(repair_review_path, store.repo_root),
        repair_review_sha256=sha256_path(repair_review_path),
        job=job,
    )


def _load_entry(
    manifest_path: Path,
    source_id: str,
) -> DeepAuditManifestEntry:
    manifest = DeepAuditManifest.model_validate_json(
        manifest_path.read_text(encoding="utf-8-sig")
    )
    matching = [
        entry
        for entry in manifest.entries
        if entry.get("source_id") == source_id
        and entry.get("status") == "prepared"
    ]
    if len(matching) != 1:
        message = f"expected one prepared deep-audit entry for {source_id}"
        raise ValueError(message)
    return DeepAuditManifestEntry.model_validate(matching[0])


def _validate_entry_files(
    repo_root: Path,
    entry: DeepAuditManifestEntry,
) -> None:
    expected: list[tuple[str, str]] = [
        (entry.english_path, entry.source_sha256),
        (entry.chinese_path, entry.candidate_sha256),
        (
            entry.normalized_candidate_path,
            entry.normalized_candidate_sha256,
        ),
    ]
    if entry.review_workflow_version == _REVIEW_WORKFLOW_V3:
        v3_artifacts = (
            (entry.preflight_path, entry.preflight_sha256),
            (entry.history_path, entry.history_sha256),
            (entry.v3_context_path, entry.v3_context_sha256),
            (entry.v3_plan_path, entry.v3_plan_sha256),
        )
        if any(
            path_value is None or sha256_value is None
            for path_value, sha256_value in v3_artifacts
        ):
            message = "v3 deep-audit manifest entry lacks evidence artifacts"
            raise ValueError(message)
        expected.extend(
            (path_value, sha256_value)
            for path_value, sha256_value in v3_artifacts
            if path_value is not None and sha256_value is not None
        )
    for path_value, expected_sha256 in expected:
        path = resolve_repo_path(repo_root, path_value)
        if sha256_path(path) != expected_sha256:
            message = f"deep-audit manifest hash changed: {path_value}"
            raise ValueError(message)
    if entry.audit_contract_version == _COVERAGE_CONTRACT_VERSION:
        contract = entry.coverage_contract
        if contract is None:
            message = "v2 deep-audit manifest entry has no coverage contract"
            raise ValueError(message)
        validate_coverage_contract(
            contract,
            english_path=resolve_repo_path(repo_root, entry.english_path),
            chinese_path=resolve_repo_path(repo_root, entry.chinese_path),
        )


def _validate_report(
    *,
    repo_root: Path,
    report: dict[str, object],
    report_path: Path,
    entry: DeepAuditManifestEntry,
    assigned_reviewer: AssignedReviewer,
) -> Literal["pass", "warn", "fail"]:
    if entry.audit_contract_version == _COVERAGE_CONTRACT_VERSION:
        return _validate_v2_report(
            repo_root=repo_root,
            report=report,
            report_path=report_path,
            entry=entry,
            assigned_reviewer=assigned_reviewer,
        )
    if report.get("source_id") != entry.source_id:
        message = "deep-audit report source_id does not match its manifest"
        raise ValueError(message)
    if report.get("review_model") != assigned_reviewer:
        message = "deep-audit report does not match its assigned reviewer"
        raise ValueError(message)
    verdict = _report_verdict(report)
    _validate_report_hashes(report, entry)
    _validate_report_paths(report, entry)
    if not _report_reached_eof(report):
        message = "deep-audit report did not prove true EOF"
        raise ValueError(message)
    issues = report.get("issues")
    if not isinstance(issues, list):
        message = "deep-audit report issues must be a list"
        raise TypeError(message)
    if verdict == "pass" and issues:
        message = "passing deep-audit report contains issues"
        raise ValueError(message)
    if verdict != "pass" and not issues:
        message = "non-passing deep-audit report has no issues"
        raise ValueError(message)
    if assigned_reviewer == "grok-4.5":
        _validate_grok_structure_counts(repo_root, report, entry)
    if not report_path.is_file():
        message = "deep-audit report disappeared during validation"
        raise ValueError(message)
    return verdict


def _validate_v2_report(
    *,
    repo_root: Path,
    report: dict[str, object],
    report_path: Path,
    entry: DeepAuditManifestEntry,
    assigned_reviewer: AssignedReviewer,
) -> Literal["pass", "warn", "fail"]:
    contract = entry.coverage_contract
    if contract is None:
        message = "v2 deep-audit manifest entry has no coverage contract"
        raise ValueError(message)
    coverage_report = validate_coverage_report(
        report,
        contract=contract,
        assigned_reviewer=assigned_reviewer,
        english_path=resolve_repo_path(repo_root, entry.english_path),
        chinese_path=resolve_repo_path(repo_root, entry.chinese_path),
    )
    if not report_path.is_file():
        message = "deep-audit report disappeared during validation"
        raise ValueError(message)
    return coverage_report.verdict


def _report_verdict(
    report: dict[str, object],
) -> Literal["pass", "warn", "fail"]:
    verdict_value = report.get("verdict", report.get("status"))
    if verdict_value not in {"pass", "warn", "fail"}:
        message = "deep-audit report has no valid verdict"
        raise ValueError(message)
    return cast("Literal['pass', 'warn', 'fail']", verdict_value)


def _validate_grok_structure_counts(
    repo_root: Path,
    report: dict[str, object],
    entry: DeepAuditManifestEntry,
) -> None:
    claimed = report.get("structure_counts")
    if not isinstance(claimed, dict):
        message = "Grok deep audit has no structure counts"
        raise TypeError(message)
    claimed_counts = cast("dict[str, object]", claimed)
    actual = review_structure_counts(
        resolve_repo_path(repo_root, entry.english_path),
        resolve_repo_path(repo_root, entry.chinese_path),
    ).model_dump()
    if claimed_counts != actual:
        message = "Grok deep-audit structure counts do not match files"
        raise ValueError(message)


def _validate_report_hashes(
    report: dict[str, object],
    entry: DeepAuditManifestEntry,
) -> None:
    expected_pairs = (
        ("source_sha256", entry.source_sha256),
        ("candidate_sha256", entry.candidate_sha256),
        ("expected_source_sha256", entry.source_sha256),
        ("actual_source_sha256", entry.source_sha256),
        ("expected_candidate_sha256", entry.candidate_sha256),
        ("actual_candidate_sha256", entry.candidate_sha256),
    )
    direct_fields = 0
    for field, expected in expected_pairs:
        value = report.get(field)
        if value is None:
            continue
        direct_fields += 1
        if value != expected:
            message = f"deep-audit report {field} does not match the manifest"
            raise ValueError(message)
    for group_name in ("expected_hashes", "actual_hashes"):
        group_value = report.get(group_name)
        if not isinstance(group_value, dict):
            continue
        group = cast("dict[str, object]", group_value)
        direct_fields += 2
        if group.get("en") != entry.source_sha256:
            message = f"deep-audit report {group_name}.en hash mismatch"
            raise ValueError(message)
        if group.get("zh-CN") != entry.candidate_sha256:
            message = f"deep-audit report {group_name}.zh-CN hash mismatch"
            raise ValueError(message)
    if direct_fields < _MIN_HASH_BINDINGS:
        message = "deep-audit report does not bind both reviewed file hashes"
        raise ValueError(message)


def _validate_report_paths(
    report: dict[str, object],
    entry: DeepAuditManifestEntry,
) -> None:
    expected = (
        ("english_path", entry.english_path),
        ("chinese_path", entry.chinese_path),
        ("candidate_path", entry.chinese_path),
    )
    for field, path_value in expected:
        value = report.get(field)
        if value is not None and value != path_value:
            message = f"deep-audit report {field} does not match its manifest"
            raise ValueError(message)


def _report_reached_eof(report: dict[str, object]) -> bool:
    if report.get("reached_real_eof") is True:
        return True
    eof = report.get("eof_verification")
    if not isinstance(eof, dict):
        return False
    eof_record = cast("dict[str, object]", eof)
    if eof_record.get("complete_to_eof") is True:
        return True
    language_records: list[dict[str, object]] = []
    for key, value in eof_record.items():
        if (
            key in {"en", "english", "zh-CN", "chinese"}
            and isinstance(value, dict)
        ):
            language_records.append(cast("dict[str, object]", value))
    return len(language_records) >= _MIN_EOF_LANGUAGE_RECORDS and all(
        value.get("true_eof_confirmed") is True
        for value in language_records
    )


def _repair_issue_draft(
    value: object,
    *,
    index: int,
    raw_source: str,
    raw_candidate: str,
    assigned_reviewer: AssignedReviewer,
) -> RepairIssueDraft:
    if not isinstance(value, dict):
        message = f"deep-audit issue {index} is not an object"
        raise TypeError(message)
    issue = cast("dict[str, object]", value)
    severity = _severity(issue.get("severity"))
    category = str(issue.get("category") or "").strip()
    location = str(issue.get("location") or "").strip()
    reviewed_source_excerpt = str(issue.get("source_excerpt") or "")
    reviewed_candidate_span = str(
        issue.get("candidate_span_text")
        or issue.get("chinese_excerpt")
        or ""
    )
    source_excerpt, candidate_span_text = map_reviewed_excerpts_to_raw(
        reviewed_source_excerpt=reviewed_source_excerpt,
        reviewed_candidate_span=reviewed_candidate_span,
        raw_source=raw_source,
        raw_candidate=raw_candidate,
    )
    explanation = str(
        issue.get("explanation")
        or issue.get("description")
        or ""
    ).strip()
    required = (
        category,
        location,
        source_excerpt,
        candidate_span_text,
        explanation,
    )
    if not all(required):
        message = f"deep-audit issue {index} lacks exact repair evidence"
        raise ValueError(message)
    return RepairIssueDraft(
        source_issue_refs=(
            str(issue.get("issue_id") or f"{assigned_reviewer}:{index}"),
        ),
        severity=severity,
        category=category,
        location=location,
        source_excerpt=source_excerpt,
        candidate_span_text=candidate_span_text,
        explanation=explanation,
    )


def map_reviewed_excerpts_to_raw(
    *,
    reviewed_source_excerpt: str,
    reviewed_candidate_span: str,
    raw_source: str,
    raw_candidate: str,
) -> tuple[str, str]:
    """Map one public-shape issue to unique repair-shape source spans."""
    if not reviewed_source_excerpt.strip():
        message = "deep-audit English source_excerpt is empty"
        raise ValueError(message)
    if not reviewed_candidate_span.strip():
        message = "deep-audit candidate span is empty"
        raise ValueError(message)
    return (
        _map_source_excerpt(reviewed_source_excerpt, raw_source),
        _map_candidate_span(reviewed_candidate_span, raw_candidate),
    )


def _map_source_excerpt(reviewed_excerpt: str, raw_source: str) -> str:
    """Map visible Markdown link text back to one exact raw source span."""
    if raw_source.count(reviewed_excerpt) == 1:
        return reviewed_excerpt
    raw_title = _map_public_title(
        reviewed_excerpt,
        raw_source,
        public_prefix=_PUBLIC_ENGLISH_TITLE_PREFIX,
    )
    if raw_title is not None:
        return raw_title

    visible_parts: list[str] = []
    raw_starts: list[int] = []
    raw_ends: list[int] = []
    link_ranges: list[tuple[int, int]] = []
    raw_cursor = 0
    visible_cursor = 0

    for match in _MARKDOWN_LINK.finditer(raw_source):
        plain = raw_source[raw_cursor : match.start()]
        visible_parts.append(plain)
        raw_starts.extend(range(raw_cursor, match.start()))
        raw_ends.extend(range(raw_cursor + 1, match.start() + 1))
        visible_cursor += len(plain)

        label = match.group(1)
        label_start = visible_cursor
        visible_parts.append(label)
        label_raw_start = match.start() + 1
        for offset, _character in enumerate(label):
            raw_starts.append(
                match.start() if offset == 0 else label_raw_start + offset
            )
            raw_ends.append(
                match.end()
                if offset == len(label) - 1
                else label_raw_start + offset + 1
            )
        visible_cursor += len(label)
        link_ranges.append((label_start, visible_cursor))
        raw_cursor = match.end()

    tail = raw_source[raw_cursor:]
    visible_parts.append(tail)
    raw_starts.extend(range(raw_cursor, len(raw_source)))
    raw_ends.extend(range(raw_cursor + 1, len(raw_source) + 1))
    visible_source = "".join(visible_parts)

    resolved_visible = recover_unique_whitespace_span(
        visible_source,
        reviewed_excerpt,
        issue_id="deep-audit-bridge",
        field_name="English source_excerpt",
    )
    visible_start = visible_source.index(resolved_visible)
    visible_end = visible_start + len(resolved_visible)
    for link_start, link_end in link_ranges:
        overlaps = visible_start < link_end and visible_end > link_start
        contains = visible_start <= link_start and visible_end >= link_end
        if overlaps and not contains:
            message = "deep-audit English excerpt contains a partial Markdown link"
            raise ValueError(message)
    raw_excerpt = raw_source[
        raw_starts[visible_start] : raw_ends[visible_end - 1]
    ]
    if raw_source.count(raw_excerpt) != 1:
        message = "mapped deep-audit English excerpt is not unique"
        raise ValueError(message)
    return raw_excerpt


def _map_candidate_span(reviewed_span: str, raw_candidate: str) -> str:
    """Map a public span back to raw only across deterministic local fragments."""
    direct_matches = raw_candidate.count(reviewed_span)
    if direct_matches == 1:
        return reviewed_span
    if direct_matches > 1:
        message = (
            "deep-audit candidate span is not unique in the raw candidate: "
            f"{direct_matches} matches"
        )
        raise ValueError(message)
    raw_title = _map_public_title(
        reviewed_span,
        raw_candidate,
        public_prefix=_PUBLIC_CHINESE_TITLE_PREFIX,
    )
    if raw_title is not None:
        return raw_title
    pattern_parts: list[str] = []
    cursor = 0
    for match in _SAME_PAGE_LINK_TARGET.finditer(reviewed_span):
        pattern_parts.append(re.escape(reviewed_span[cursor : match.start()]))
        pattern_parts.append(r"\]\(#[^)]+\)")
        cursor = match.end()
    if not pattern_parts:
        message = (
            "deep-audit candidate span is absent from the raw candidate "
            "and has no deterministic same-page fragment mapping"
        )
        raise ValueError(message)
    pattern_parts.append(re.escape(reviewed_span[cursor:]))
    matches = tuple(
        match.group(0)
        for match in re.finditer("".join(pattern_parts), raw_candidate)
    )
    if len(matches) != 1:
        message = (
            "deep-audit candidate span has no unique raw mapping after "
            f"same-page fragment normalization: {len(matches)} matches"
        )
        raise ValueError(message)
    return matches[0]


def _map_public_title(
    reviewed_span: str,
    raw_text: str,
    *,
    public_prefix: str,
) -> str | None:
    """Reverse only the deterministic language prefix added at materialization."""
    if "\n" in reviewed_span or not reviewed_span.startswith(public_prefix):
        return None
    raw_span = f"title: {reviewed_span.removeprefix(public_prefix)}"
    if raw_text.count(raw_span) != 1:
        message = "materialized title has no unique raw frontmatter mapping"
        raise ValueError(message)
    return raw_span


def _severity(value: object) -> Literal["high", "medium", "low"]:
    normalized = str(value or "").strip().lower()
    mapped = {
        "critical": "high",
        "major": "high",
        "high": "high",
        "medium": "medium",
        "minor": "medium",
        "low": "low",
    }.get(normalized)
    if mapped is None:
        message = f"unsupported deep-audit issue severity: {normalized or '<empty>'}"
        raise ValueError(message)
    return cast("Literal['high', 'medium', 'low']", mapped)


def _repo_relative(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError as exc:
        message = "deep-audit artifact path escapes the repository"
        raise ValueError(message) from exc
