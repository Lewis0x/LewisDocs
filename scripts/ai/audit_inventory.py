# Copyright 2026

"""Deterministic inventory and controlled admission for deep audits."""

from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from dataclasses import dataclass
from enum import StrEnum
from itertools import product as cartesian_product
from math import ceil
from typing import TYPE_CHECKING, ClassVar, Final, Literal, Self, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from scripts.ai.errors import AIAgentError
from scripts.ai.manifest import load_sources
from scripts.ai.page_format import AcceptedPage, parse_accepted_page
from scripts.ai.pipeline import TERMINAL_STATES, PipelineStore
from scripts.ai.pipeline_intake import AuditIntakeState, AuditIntakeStore
from scripts.ai.review_contract import AssignedReviewer, sha256_path, sha256_text

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence
    from pathlib import Path

INVENTORY_VERSION: Final = 1
ASSIGNMENT_VERSION: Final = 1
_ASSIGNMENT_SALT: Final = "lewisdocs-audit-admission-v1"
_SOURCE_ID_RE: Final = re.compile(r"^(?:claude-code|codex)/[a-z0-9][a-z0-9/-]*$")
_HEADING_RE: Final = re.compile(r"^\s{0,3}#{1,6}\s+\S")
_FENCE_RE: Final = re.compile(r"^\s{0,3}(?P<marker>`{3,}|~{3,})")
_LINK_RE: Final = re.compile(r"(?<!!)\[[^\]\n]+\]\([^)]+\)")
_MDX_TAG_RE: Final = re.compile(r"</?[A-Za-z][A-Za-z0-9.-]*(?:\s|/?>)")
_REVIEWERS: Final[tuple[AssignedReviewer, ...]] = (
    "gpt-5.6-terra",
    "grok-4.5",
)
Product = Literal["claude-code", "codex"]
_PRODUCTS: Final[tuple[Product, ...]] = ("claude-code", "codex")
_INTAKE_TERMINAL_STATES: Final[frozenset[AuditIntakeState]] = frozenset(
    {
        AuditIntakeState.QUEUED_TO_REPAIR,
        AuditIntakeState.CLEAN_ADOPTED,
        AuditIntakeState.STRUCTURAL_BLOCKED,
        AuditIntakeState.INVALID,
    }
)
_OFFICIAL_VERIFIED_STATUSES: Final = frozenset({"ready", "applied"})
_MAX_PILOT_PAGES: Final = 12
_MIN_DIVERSE_CAPACITY: Final = 2

__all__ = (
    "AuditInventory",
    "AuditInventoryItem",
    "CanonicalSourceState",
    "InventorySource",
    "InventoryStatus",
    "PilotBatch",
    "PilotLane",
    "PilotSelection",
    "ReviewScan",
    "ReviewSourceEvidence",
    "build_inventory",
    "build_inventory_from_sources",
    "collect_canonical_states",
    "collect_verified_official_source_ids",
    "scan_review_evidence",
    "select_pilot",
    "stable_reviewer",
    "write_inventory_atomic",
)


class InventoryStatus(StrEnum):
    """Exactly one admission status for every manifest source."""

    FORMAL_VALID = "formal_valid"
    CURRENT_PIPELINE = "current_pipeline"
    LEGACY_ISOLATED = "legacy_isolated"
    MISSING_SOURCE = "missing_source"
    MISSING_NORMALIZED = "missing_normalized"
    ELIGIBLE_ASSIGNED = "eligible_assigned"
    ELIGIBLE_UNASSIGNED = "eligible_unassigned"
    REVIEWER_CONFLICT = "reviewer_conflict"


class _StrictModel(BaseModel):
    """Immutable, extra-forbidding output contract."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )


class InventorySource(_StrictModel):
    """Public manifest identity needed by inventory classification."""

    source_id: str
    product: Literal["claude-code", "codex"]
    title: str = Field(min_length=1)

    @field_validator("source_id")
    @classmethod
    def _safe_source_id(cls, value: str) -> str:
        if _SOURCE_ID_RE.fullmatch(value) is None or ".." in value:
            message = "inventory source_id is not a safe manifest route"
            raise ValueError(message)
        expected_product = value.split("/", 1)[0]
        if expected_product not in {"claude-code", "codex"}:
            message = "inventory source_id has an unsupported product"
            raise ValueError(message)
        return value

    @model_validator(mode="after")
    def _product_matches_source_id(self) -> Self:
        if not self.source_id.startswith(f"{self.product}/"):
            message = "inventory product does not match source_id"
            raise ValueError(message)
        return self


class CanonicalSourceState(_StrictModel):
    """Secret-free current or terminal canonical store state."""

    kind: Literal["pipeline", "audit_intake"]
    record_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    state: str = Field(min_length=1)
    terminal: bool
    assigned_reviewer: AssignedReviewer


class ReviewSourceEvidence(_StrictModel):
    """Reviewer ownership and isolation evidence from legacy reports."""

    source_id: str
    reviewers: tuple[AssignedReviewer, ...] = ()
    reviewer_report_count: int = Field(default=0, ge=0)
    legacy_isolated: bool = False
    isolated_report_count: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def _reviewers_are_unique_and_ordered(self) -> Self:
        if self.reviewers != _ordered_reviewers(self.reviewers):
            message = "review evidence models are not unique and ordered"
            raise ValueError(message)
        return self


class ReviewScan(_StrictModel):
    """Sanitized aggregate of a recursive review JSON scan."""

    version: Literal[1] = 1
    files_scanned: int = Field(ge=0)
    exact_source_reports: int = Field(ge=0)
    ignored_malformed: int = Field(ge=0)
    ignored_unknown_source: int = Field(ge=0)
    ignored_without_reviewer: int = Field(ge=0)
    evidence: tuple[ReviewSourceEvidence, ...] = ()

    @model_validator(mode="after")
    def _source_evidence_is_unique(self) -> Self:
        source_ids = tuple(item.source_id for item in self.evidence)
        if len(source_ids) != len(set(source_ids)):
            message = "review scan contains duplicate source evidence"
            raise ValueError(message)
        return self


class AuditInventoryItem(_StrictModel):
    """One conserved manifest source with admission and workload evidence."""

    version: Literal[1] = 1
    source_id: str
    product: Literal["claude-code", "codex"]
    title: str
    status: InventoryStatus
    canonical_states: tuple[CanonicalSourceState, ...] = ()
    reviewer_evidence: tuple[AssignedReviewer, ...] = ()
    reviewer_conflict: bool = False
    historical_reviewer: AssignedReviewer | None = None
    admission_reviewer: AssignedReviewer | None = None
    reviewer_assignment_basis: Literal[
        "canonical_or_review",
        "stable_sha256",
        "conflict",
        "none",
    ]
    legacy_isolated: bool = False
    official_localization_verified: bool = False
    english_path: str
    english_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    normalized_candidate_path: str
    normalized_candidate_sha256: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )
    formal_target_path: str
    formal_target_sha256: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )
    translation_model: str | None = None
    translation_provider: Literal["kimi", "glm", "gpt", "official"] | None = None
    english_characters: int = Field(default=0, ge=0)
    chinese_characters: int = Field(default=0, ge=0)
    english_headings: int = Field(default=0, ge=0)
    chinese_headings: int = Field(default=0, ge=0)
    estimated_work_units: int = Field(default=0, ge=0)
    structure_risk_score: int = Field(default=0, ge=0)

    @field_validator(
        "english_path",
        "normalized_candidate_path",
        "formal_target_path",
    )
    @classmethod
    def _paths_are_sanitized(cls, value: str) -> str:
        return _require_relative_inventory_path(value)

    @model_validator(mode="after")
    def _admission_contract_is_consistent(self) -> Self:
        if self.reviewer_conflict != (len(self.reviewer_evidence) > 1):
            message = "reviewer conflict flag does not match evidence"
            raise ValueError(message)
        if len(self.reviewer_evidence) == 1:
            if self.historical_reviewer != self.reviewer_evidence[0]:
                message = "unique reviewer evidence was not preserved"
                raise ValueError(message)
        elif self.historical_reviewer is not None:
            message = "historical reviewer requires unique evidence"
            raise ValueError(message)
        eligible = self.status in {
            InventoryStatus.ELIGIBLE_ASSIGNED,
            InventoryStatus.ELIGIBLE_UNASSIGNED,
        }
        if eligible:
            required = (
                self.english_sha256,
                self.normalized_candidate_sha256,
                self.admission_reviewer,
            )
            if any(value is None for value in required):
                message = "eligible inventory item lacks source, candidate, or reviewer"
                raise ValueError(message)
            if self.estimated_work_units < 1:
                message = "eligible inventory item has no estimated work"
                raise ValueError(message)
        elif self.reviewer_assignment_basis == "stable_sha256" or (
            self.historical_reviewer is None and self.admission_reviewer is not None
        ):
            message = "stable admission assignment is only valid for eligible pages"
            raise ValueError(message)
        if self.status == InventoryStatus.REVIEWER_CONFLICT and not self.reviewer_conflict:
            message = "reviewer_conflict status lacks conflicting evidence"
            raise ValueError(message)
        return self


class AuditInventory(_StrictModel):
    """Versioned, conserved, deterministic inventory output."""

    version: Literal[1] = INVENTORY_VERSION
    assignment_version: Literal[1] = ASSIGNMENT_VERSION
    manifest_path: str
    manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    manifest_order_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_count: int = Field(ge=0)
    unknown_source_count: Literal[0] = 0
    status_counts: dict[str, int]
    review_scan: ReviewScan
    items: tuple[AuditInventoryItem, ...]

    @field_validator("manifest_path")
    @classmethod
    def _manifest_path_is_sanitized(cls, value: str) -> str:
        return _require_relative_inventory_path(value)

    @model_validator(mode="after")
    def _all_manifest_sources_are_conserved(self) -> Self:
        source_ids = tuple(item.source_id for item in self.items)
        if len(source_ids) != len(set(source_ids)):
            message = "inventory contains duplicate source_id values"
            raise ValueError(message)
        if self.source_count != len(source_ids):
            message = "inventory source_count does not match items"
            raise ValueError(message)
        if self.manifest_order_sha256 != _source_order_sha256(source_ids):
            message = "inventory manifest order hash does not match items"
            raise ValueError(message)
        expected_keys = {status.value for status in InventoryStatus}
        if set(self.status_counts) != expected_keys:
            message = "inventory status_counts does not cover every status"
            raise ValueError(message)
        actual = {status.value: 0 for status in InventoryStatus}
        for item in self.items:
            actual[item.status.value] += 1
        if self.status_counts != actual:
            message = "inventory status_counts does not match items"
            raise ValueError(message)
        if sum(self.status_counts.values()) != self.source_count:
            message = "inventory status conservation failed"
            raise ValueError(message)
        return self


class PilotSelection(_StrictModel):
    """One admitted page with its fixed reviewer and LPT lane."""

    source_id: str
    product: Product
    reviewer: AssignedReviewer
    lane_index: int = Field(ge=0)
    estimated_work_units: int = Field(ge=1)
    structure_risk_score: int = Field(ge=0)
    official_localization_verified: bool
    reviewer_assignment_basis: Literal["canonical_or_review", "stable_sha256"]

    @model_validator(mode="after")
    def _product_matches_source_id(self) -> Self:
        if not self.source_id.startswith(f"{self.product}/"):
            message = "pilot product does not match source_id"
            raise ValueError(message)
        return self


class PilotLane(_StrictModel):
    """One model-specific worker lane after LPT placement."""

    reviewer: AssignedReviewer
    lane_index: int = Field(ge=0)
    source_ids: tuple[str, ...]
    total_work_units: int = Field(ge=0)


class PilotBatch(_StrictModel):
    """A bounded, reviewer-preserving pilot admission batch."""

    version: Literal[1] = 1
    max_pages: int = Field(ge=1, le=12)
    reviewer_limits: dict[AssignedReviewer, int]
    manifest_product_counts: dict[Product, int]
    product_targets: dict[Product, int]
    selected_count: int = Field(ge=0, le=12)
    reviewer_counts: dict[AssignedReviewer, int]
    product_counts: dict[Product, int]
    excluded_source_ids: tuple[str, ...] = ()
    selections: tuple[PilotSelection, ...]
    lanes: tuple[PilotLane, ...]

    @model_validator(mode="after")
    def _selection_is_unique_and_within_limits(self) -> Self:
        source_ids = tuple(selection.source_id for selection in self.selections)
        if len(source_ids) != len(set(source_ids)):
            message = "pilot batch contains duplicate source_id values"
            raise ValueError(message)
        if self.excluded_source_ids != tuple(
            sorted(set(self.excluded_source_ids))
        ):
            message = "pilot excluded source ids must be unique and sorted"
            raise ValueError(message)
        if set(source_ids) & set(self.excluded_source_ids):
            message = "pilot selected an explicitly excluded source_id"
            raise ValueError(message)
        if self.selected_count != len(self.selections):
            message = "pilot selected_count does not match selections"
            raise ValueError(message)
        if self.selected_count > self.max_pages:
            message = "pilot batch exceeds max_pages"
            raise ValueError(message)
        actual: dict[AssignedReviewer, int] = {
            "gpt-5.6-terra": 0,
            "grok-4.5": 0,
        }
        for selection in self.selections:
            actual[selection.reviewer] += 1
        if self.reviewer_counts != actual:
            message = "pilot reviewer_counts does not match selections"
            raise ValueError(message)
        if any(actual[reviewer] > self.reviewer_limits[reviewer] for reviewer in _REVIEWERS):
            message = "pilot reviewer limit exceeded"
            raise ValueError(message)
        _validate_pilot_products(self)
        lane_sources = tuple(source_id for lane in self.lanes for source_id in lane.source_ids)
        if sorted(lane_sources) != sorted(source_ids):
            message = "pilot lane placement does not cover selections exactly once"
            raise ValueError(message)
        return self


@dataclass(frozen=True)
class _MarkdownMetrics:
    characters: int
    headings: int
    fenced_blocks: int
    links: int
    mdx_tags: int


@dataclass(frozen=True)
class _PageEvidence:
    page: AcceptedPage
    sha256: str
    metrics: _MarkdownMetrics


def stable_reviewer(source_id: str) -> AssignedReviewer:
    """Assign an unowned source deterministically without consulting WIP."""
    _require_source_id(source_id)
    digest = hashlib.sha256(f"{_ASSIGNMENT_SALT}\0{source_id}".encode()).digest()
    return _REVIEWERS[digest[0] & 1]


def scan_review_evidence(
    repo_root: Path,
    source_ids: Iterable[str],
    *,
    reviews_root: Path | None = None,
) -> ReviewScan:
    """Scan only top-level exact source_id and Terra/Grok ownership fields."""
    root = repo_root.resolve()
    known = frozenset(source_ids)
    for source_id in known:
        _require_source_id(source_id)
    review_root = (
        reviews_root if reviews_root is not None else root / ".ai-local/reviews"
    ).resolve()
    _ = _repo_relative(root, review_root)
    reviewers: dict[str, set[AssignedReviewer]] = {}
    report_counts: dict[str, int] = {}
    isolated_counts: dict[str, int] = {}
    files_scanned = 0
    exact_source_reports = 0
    ignored_malformed = 0
    ignored_unknown_source = 0
    ignored_without_reviewer = 0
    paths = sorted(review_root.rglob("*.json")) if review_root.is_dir() else []
    for path in paths:
        if not path.is_file():
            continue
        files_scanned += 1
        document = _read_json_object(path)
        if document is None:
            ignored_malformed += 1
            continue
        source_id = document.get("source_id")
        if not isinstance(source_id, str) or source_id not in known:
            ignored_unknown_source += 1
            continue
        exact_source_reports += 1
        found = _reviewers_in_document(document)
        isolated = document.get("status") == "isolated"
        if not found:
            ignored_without_reviewer += 1
        else:
            reviewers.setdefault(source_id, set()).update(found)
            report_counts[source_id] = report_counts.get(source_id, 0) + 1
        if isolated:
            isolated_counts[source_id] = isolated_counts.get(source_id, 0) + 1
    evidence = tuple(
        ReviewSourceEvidence(
            source_id=source_id,
            reviewers=_ordered_reviewers(reviewers.get(source_id, set())),
            reviewer_report_count=report_counts.get(source_id, 0),
            legacy_isolated=isolated_counts.get(source_id, 0) > 0,
            isolated_report_count=isolated_counts.get(source_id, 0),
        )
        for source_id in sorted(reviewers.keys() | isolated_counts.keys())
    )
    return ReviewScan(
        files_scanned=files_scanned,
        exact_source_reports=exact_source_reports,
        ignored_malformed=ignored_malformed,
        ignored_unknown_source=ignored_unknown_source,
        ignored_without_reviewer=ignored_without_reviewer,
        evidence=evidence,
    )


def collect_canonical_states(
    pipeline_store: PipelineStore,
    intake_store: AuditIntakeStore,
    source_ids: Iterable[str],
) -> tuple[tuple[str, tuple[CanonicalSourceState, ...]], ...]:
    """Read active and terminal snapshots from both canonical stores."""
    known = frozenset(source_ids)
    records: dict[str, list[CanonicalSourceState]] = {}
    for job in pipeline_store.list_jobs():
        if job.source_id not in known:
            message = f"pipeline contains source outside manifest: {job.source_id}"
            raise ValueError(message)
        records.setdefault(job.source_id, []).append(
            CanonicalSourceState(
                kind="pipeline",
                record_id=job.job_id,
                state=job.state.value,
                terminal=job.state in TERMINAL_STATES,
                assigned_reviewer=job.assigned_reviewer,
            )
        )
    for item in intake_store.list_items():
        if item.source_id not in known:
            message = f"audit intake contains source outside manifest: {item.source_id}"
            raise ValueError(message)
        records.setdefault(item.source_id, []).append(
            CanonicalSourceState(
                kind="audit_intake",
                record_id=item.intake_id,
                state=item.state.value,
                terminal=item.state in _INTAKE_TERMINAL_STATES,
                assigned_reviewer=item.assigned_reviewer,
            )
        )
    return tuple(
        (
            source_id,
            tuple(
                sorted(
                    values,
                    key=lambda value: (
                        value.kind,
                        value.record_id,
                        value.state,
                    ),
                )
            ),
        )
        for source_id, values in sorted(records.items())
    )


def collect_verified_official_source_ids(
    repo_root: Path,
    source_ids: Iterable[str],
) -> frozenset[str]:
    """Read existing local sync evidence without contacting official sites."""
    root = repo_root.resolve()
    known = frozenset(source_ids)
    report_paths = {
        root / ".ai-local/official-chinese-sync-report.json",
        *(
            (root / ".ai-local/official-chinese-sync-history").rglob(
                "official-chinese-sync-report.json"
            )
            if (root / ".ai-local/official-chinese-sync-history").is_dir()
            else ()
        ),
    }
    verified: set[str] = set()
    for path in sorted(report_paths):
        if not path.is_file():
            continue
        document = _read_json_object(path)
        if document is None:
            continue
        results = document.get("results")
        if not isinstance(results, list):
            continue
        for result in cast("list[object]", results):
            if not isinstance(result, dict):
                continue
            result_object = cast("dict[object, object]", result)
            source_id = result_object.get("source_id")
            status = result_object.get("status")
            if (
                isinstance(source_id, str)
                and source_id in known
                and status in _OFFICIAL_VERIFIED_STATUSES
            ):
                verified.add(source_id)
    return frozenset(verified)


def build_inventory(  # noqa: PLR0913
    repo_root: Path,
    *,
    manifest_path: Path | None = None,
    pipeline_store: PipelineStore | None = None,
    intake_store: AuditIntakeStore | None = None,
    reviews_root: Path | None = None,
    normalized_root: Path | None = None,
    formal_root: Path | None = None,
) -> AuditInventory:
    """Build one deterministic inventory from the repository's current state."""
    root = repo_root.resolve()
    source_manifest_path = (
        manifest_path if manifest_path is not None else root / "source-ai/sources.yaml"
    ).resolve()
    relative_manifest = _repo_relative(root, source_manifest_path)
    manifest = load_sources(source_manifest_path)
    sources = tuple(
        InventorySource(
            source_id=str(source.id),
            product=source.product,
            title=source.title,
        )
        for source in manifest.root
    )
    store = pipeline_store or PipelineStore(root / ".ai-local/pipeline-v1", root)
    intake = intake_store or AuditIntakeStore(store)
    source_ids = tuple(source.source_id for source in sources)
    canonical = collect_canonical_states(store, intake, source_ids)
    reviews = scan_review_evidence(root, source_ids, reviews_root=reviews_root)
    official_verified = collect_verified_official_source_ids(root, source_ids)
    return build_inventory_from_sources(
        root,
        sources,
        manifest_path=relative_manifest,
        manifest_sha256=sha256_path(source_manifest_path),
        canonical_states=canonical,
        review_scan=reviews,
        official_verified_source_ids=official_verified,
        normalized_root=normalized_root,
        formal_root=formal_root,
    )


def build_inventory_from_sources(  # noqa: PLR0913
    repo_root: Path,
    sources: Sequence[InventorySource],
    *,
    manifest_path: str,
    manifest_sha256: str,
    canonical_states: Iterable[tuple[str, tuple[CanonicalSourceState, ...]]] = (),
    review_scan: ReviewScan | None = None,
    official_verified_source_ids: Iterable[str] = (),
    normalized_root: Path | None = None,
    formal_root: Path | None = None,
) -> AuditInventory:
    """Purely classify explicit sources from immutable local evidence."""
    root = repo_root.resolve()
    source_ids = tuple(source.source_id for source in sources)
    if len(source_ids) != len(set(source_ids)):
        message = "inventory input contains duplicate manifest source_id values"
        raise ValueError(message)
    known = frozenset(source_ids)
    canonical_rows = tuple(canonical_states)
    canonical_source_ids = tuple(source_id for source_id, _ in canonical_rows)
    if len(canonical_source_ids) != len(set(canonical_source_ids)):
        message = "canonical inventory evidence contains duplicate source_id values"
        raise ValueError(message)
    canonical_by_source = dict(canonical_rows)
    unknown_canonical = set(canonical_by_source) - known
    if unknown_canonical:
        message = "canonical inventory evidence contains an unknown source_id"
        raise ValueError(message)
    reviews = review_scan or ReviewScan(
        files_scanned=0,
        exact_source_reports=0,
        ignored_malformed=0,
        ignored_unknown_source=0,
        ignored_without_reviewer=0,
    )
    review_by_source = {evidence.source_id: evidence for evidence in reviews.evidence}
    if set(review_by_source) - known:
        message = "review inventory evidence contains an unknown source_id"
        raise ValueError(message)
    official_verified = frozenset(official_verified_source_ids)
    if official_verified - known:
        message = "official localization evidence contains an unknown source_id"
        raise ValueError(message)
    candidate_root = (
        normalized_root
        if normalized_root is not None
        else root / ".ai-local/staging/dual-review-normalized"
    ).resolve()
    target_root = (
        formal_root if formal_root is not None else root / "source-ai/content/zh-CN"
    ).resolve()
    _ = _repo_relative(root, candidate_root)
    _ = _repo_relative(root, target_root)
    items = tuple(
        _classify_source(
            root,
            source,
            canonical_by_source.get(source.source_id, ()),
            review_by_source.get(source.source_id),
            official_verified=source.source_id in official_verified,
            normalized_root=candidate_root,
            formal_root=target_root,
        )
        for source in sources
    )
    status_counts = {status.value: 0 for status in InventoryStatus}
    for item in items:
        status_counts[item.status.value] += 1
    return AuditInventory(
        manifest_path=manifest_path,
        manifest_sha256=manifest_sha256,
        manifest_order_sha256=_source_order_sha256(source_ids),
        source_count=len(sources),
        status_counts=status_counts,
        review_scan=reviews,
        items=items,
    )


def select_pilot(  # noqa: PLR0913
    inventory: AuditInventory,
    *,
    max_pages: int = 12,
    terra_limit: int = 6,
    grok_limit: int = 6,
    terra_lanes: int = 3,
    grok_lanes: int = 3,
    excluded_source_ids: Iterable[str] = (),
) -> PilotBatch:
    """Select a risk-aware 6+6 pilot and place it with deterministic LPT."""
    if not 1 <= max_pages <= _MAX_PILOT_PAGES:
        message = "pilot max_pages must be between 1 and 12"
        raise ValueError(message)
    if min(terra_limit, grok_limit, terra_lanes, grok_lanes) < 1:
        message = "pilot reviewer limits and lane counts must be positive"
        raise ValueError(message)
    terra_quota = min(terra_limit, (max_pages + 1) // 2)
    grok_quota = min(grok_limit, max_pages // 2)
    limits: dict[AssignedReviewer, int] = {
        "gpt-5.6-terra": terra_quota,
        "grok-4.5": grok_quota,
    }
    lane_counts: dict[AssignedReviewer, int] = {
        "gpt-5.6-terra": terra_lanes,
        "grok-4.5": grok_lanes,
    }
    excluded = tuple(sorted(set(excluded_source_ids)))
    eligible = tuple(
        item
        for item in inventory.items
        if item.status
        in {
            InventoryStatus.ELIGIBLE_ASSIGNED,
            InventoryStatus.ELIGIBLE_UNASSIGNED,
        }
        and item.source_id not in set(excluded)
    )
    candidates_by_reviewer: dict[
        AssignedReviewer,
        tuple[AuditInventoryItem, ...],
    ] = {
        reviewer: tuple(item for item in eligible if item.admission_reviewer == reviewer)
        for reviewer in _REVIEWERS
    }
    reviewer_capacities: dict[AssignedReviewer, int] = {
        reviewer: min(limits[reviewer], len(candidates_by_reviewer[reviewer]))
        for reviewer in _REVIEWERS
    }
    manifest_product_counts: dict[Product, int] = {
        product: sum(item.product == product for item in inventory.items) for product in _PRODUCTS
    }
    reviewer_product_targets = _allocate_reviewer_product_targets(
        candidates_by_reviewer,
        reviewer_capacities,
        manifest_product_counts,
    )
    selected_by_reviewer: dict[AssignedReviewer, tuple[AuditInventoryItem, ...]] = {}
    for reviewer in _REVIEWERS:
        selected_by_reviewer[reviewer] = _select_reviewer_candidates(
            candidates_by_reviewer[reviewer],
            reviewer_product_targets[reviewer],
        )
    selections: list[PilotSelection] = []
    lanes: list[PilotLane] = []
    for reviewer in _REVIEWERS:
        chosen = selected_by_reviewer[reviewer]
        loads = [0] * lane_counts[reviewer]
        buckets: list[list[str]] = [[] for _ in loads]
        placement: dict[str, int] = {}
        for item in sorted(
            chosen,
            key=lambda value: (-value.estimated_work_units, value.source_id),
        ):
            lane_index = min(range(len(loads)), key=lambda index: (loads[index], index))
            loads[lane_index] += item.estimated_work_units
            buckets[lane_index].append(item.source_id)
            placement[item.source_id] = lane_index
        for lane_index, source_ids in enumerate(buckets):
            lanes.append(
                PilotLane(
                    reviewer=reviewer,
                    lane_index=lane_index,
                    source_ids=tuple(source_ids),
                    total_work_units=loads[lane_index],
                )
            )
        selections.extend(
            PilotSelection(
                source_id=item.source_id,
                product=item.product,
                reviewer=reviewer,
                lane_index=placement[item.source_id],
                estimated_work_units=item.estimated_work_units,
                structure_risk_score=item.structure_risk_score,
                official_localization_verified=item.official_localization_verified,
                reviewer_assignment_basis=cast(
                    "Literal['canonical_or_review', 'stable_sha256']",
                    item.reviewer_assignment_basis,
                ),
            )
            for item in chosen
        )
    selections.sort(
        key=lambda value: (
            _reviewer_rank(value.reviewer),
            value.lane_index,
            -value.estimated_work_units,
            value.source_id,
        )
    )
    reviewer_counts: dict[AssignedReviewer, int] = {
        reviewer: len(selected_by_reviewer[reviewer]) for reviewer in _REVIEWERS
    }
    product_targets: dict[Product, int] = {
        product: sum(reviewer_product_targets[reviewer][product] for reviewer in _REVIEWERS)
        for product in _PRODUCTS
    }
    return PilotBatch(
        max_pages=max_pages,
        reviewer_limits=limits,
        manifest_product_counts=manifest_product_counts,
        product_targets=product_targets,
        selected_count=len(selections),
        reviewer_counts=reviewer_counts,
        product_counts=dict(product_targets),
        excluded_source_ids=excluded,
        selections=tuple(selections),
        lanes=tuple(lanes),
    )


def write_inventory_atomic(path: Path, inventory: AuditInventory) -> bool:
    """Atomically write deterministic JSON; return False for an exact replay."""
    payload = (inventory.model_dump_json(indent=2) + "\n").encode("utf-8")
    if path.is_file() and path.read_bytes() == payload:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("xb") as handle:
            _ = handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        _ = temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    return True


def _classify_source(  # noqa: PLR0913
    root: Path,
    source: InventorySource,
    canonical_states: tuple[CanonicalSourceState, ...],
    review: ReviewSourceEvidence | None,
    *,
    official_verified: bool,
    normalized_root: Path,
    formal_root: Path,
) -> AuditInventoryItem:
    source_id = source.source_id
    english_path = root / "source-ai/content/en" / f"{source_id}.md"
    candidate_path = normalized_root / f"{source_id}.md"
    target_path = formal_root / f"{source_id}.md"
    english = _load_page_evidence(english_path, source_id, "en")
    candidate = _load_page_evidence(candidate_path, source_id, "zh-CN")
    if (
        english is not None
        and candidate is not None
        and candidate.page.content_sha256 != english.page.content_sha256
    ):
        candidate = None
    target_sha256 = sha256_path(target_path) if target_path.is_file() else None
    formal_page = (
        _load_page_evidence(target_path, source_id, "zh-CN") if target_sha256 is not None else None
    )
    reviewer_evidence = _ordered_reviewers(
        (
            *(state.assigned_reviewer for state in canonical_states),
            *(review.reviewers if review is not None else ()),
        )
    )
    reviewer_conflict = len(reviewer_evidence) > 1
    historical_reviewer = reviewer_evidence[0] if len(reviewer_evidence) == 1 else None
    legacy_isolated = review.legacy_isolated if review is not None else False
    status = _inventory_status(
        formal_exists=target_sha256 is not None,
        has_canonical_state=bool(canonical_states),
        reviewer_conflict=reviewer_conflict,
        legacy_isolated=legacy_isolated,
        source_usable=english is not None,
        candidate_usable=candidate is not None,
        historical_reviewer=historical_reviewer,
    )
    basis, admission_reviewer = _reviewer_assignment(
        source_id,
        status,
        reviewer_conflict=reviewer_conflict,
        historical_reviewer=historical_reviewer,
    )
    metadata_page = (
        formal_page.page
        if formal_page is not None
        else candidate.page
        if candidate is not None
        else None
    )
    translation_model, translation_provider = _translation_provenance(metadata_page)
    is_official = official_verified or (
        metadata_page is not None and metadata_page.translation_source == "official"
    )
    english_metrics = english.metrics if english is not None else _empty_metrics()
    candidate_metrics = candidate.metrics if candidate is not None else _empty_metrics()
    estimated_work, structure_risk = _workload(english_metrics, candidate_metrics)
    return AuditInventoryItem(
        source_id=source_id,
        product=source.product,
        title=source.title,
        status=status,
        canonical_states=canonical_states,
        reviewer_evidence=reviewer_evidence,
        reviewer_conflict=reviewer_conflict,
        historical_reviewer=historical_reviewer,
        admission_reviewer=admission_reviewer,
        reviewer_assignment_basis=basis,
        legacy_isolated=legacy_isolated,
        official_localization_verified=is_official,
        english_path=_repo_relative(root, english_path),
        english_sha256=english.sha256 if english is not None else None,
        normalized_candidate_path=_repo_relative(root, candidate_path),
        normalized_candidate_sha256=(candidate.sha256 if candidate is not None else None),
        formal_target_path=_repo_relative(root, target_path),
        formal_target_sha256=target_sha256,
        translation_model=translation_model,
        translation_provider=translation_provider,
        english_characters=english_metrics.characters,
        chinese_characters=candidate_metrics.characters,
        english_headings=english_metrics.headings,
        chinese_headings=candidate_metrics.headings,
        estimated_work_units=estimated_work,
        structure_risk_score=structure_risk,
    )


def _load_page_evidence(
    path: Path,
    source_id: str,
    language: Literal["en", "zh-CN"],
) -> _PageEvidence | None:
    if not path.is_file():
        return None
    try:
        page = parse_accepted_page(path)
        if str(page.source_id) != source_id or page.lang != language:
            return None
        if language == "zh-CN" and str(page.translation_of) != source_id:
            return None
        return _PageEvidence(
            page=page,
            sha256=sha256_path(path),
            metrics=_markdown_metrics(page.body),
        )
    except (AIAgentError, OSError):
        return None


def _markdown_metrics(markdown: str) -> _MarkdownMetrics:
    headings = 0
    fenced_blocks = 0
    active_fence: str | None = None
    for line in markdown.splitlines():
        fence = _FENCE_RE.match(line)
        if fence is not None:
            marker = fence.group("marker")
            marker_character = marker[0]
            if active_fence is None:
                active_fence = marker_character
                fenced_blocks += 1
            elif active_fence == marker_character:
                active_fence = None
            continue
        if active_fence is None and _HEADING_RE.match(line) is not None:
            headings += 1
    return _MarkdownMetrics(
        characters=len(markdown),
        headings=headings,
        fenced_blocks=fenced_blocks,
        links=len(_LINK_RE.findall(markdown)),
        mdx_tags=len(_MDX_TAG_RE.findall(markdown)),
    )


def _workload(
    english: _MarkdownMetrics,
    chinese: _MarkdownMetrics,
) -> tuple[int, int]:
    structure_risk = (
        abs(english.headings - chinese.headings)
        + 4 * abs(english.fenced_blocks - chinese.fenced_blocks)
        + 2 * abs(english.mdx_tags - chinese.mdx_tags)
        + min(abs(english.links - chinese.links), 20)
    )
    characters = english.characters + chinese.characters
    work_units = (
        ceil(characters / 2000) + ceil(max(english.headings, chinese.headings) / 5) + structure_risk
    )
    return max(1, work_units) if characters else 0, structure_risk


def _translation_provenance(
    page: AcceptedPage | None,
) -> tuple[str | None, Literal["kimi", "glm", "gpt", "official"] | None]:
    if page is None:
        return None, None
    if page.translation_source == "official":
        return "official", "official"
    model = page.translation_model
    match model:
        case "k3":
            return model, "kimi"
        case "glm-5.2":
            return model, "glm"
        case "gpt-5.6":
            return model, "gpt"
        case None:
            return None, None


def _inventory_status(  # noqa: PLR0911, PLR0913
    *,
    formal_exists: bool,
    has_canonical_state: bool,
    reviewer_conflict: bool,
    legacy_isolated: bool,
    source_usable: bool,
    candidate_usable: bool,
    historical_reviewer: AssignedReviewer | None,
) -> InventoryStatus:
    if formal_exists:
        return InventoryStatus.FORMAL_VALID
    if has_canonical_state:
        return InventoryStatus.CURRENT_PIPELINE
    if reviewer_conflict:
        return InventoryStatus.REVIEWER_CONFLICT
    if legacy_isolated:
        return InventoryStatus.LEGACY_ISOLATED
    if not source_usable:
        return InventoryStatus.MISSING_SOURCE
    if not candidate_usable:
        return InventoryStatus.MISSING_NORMALIZED
    if historical_reviewer is not None:
        return InventoryStatus.ELIGIBLE_ASSIGNED
    return InventoryStatus.ELIGIBLE_UNASSIGNED


def _reviewer_assignment(
    source_id: str,
    status: InventoryStatus,
    *,
    reviewer_conflict: bool,
    historical_reviewer: AssignedReviewer | None,
) -> tuple[
    Literal["canonical_or_review", "stable_sha256", "conflict", "none"],
    AssignedReviewer | None,
]:
    if reviewer_conflict:
        return "conflict", None
    if historical_reviewer is not None:
        return "canonical_or_review", historical_reviewer
    if status == InventoryStatus.ELIGIBLE_UNASSIGNED:
        return "stable_sha256", stable_reviewer(source_id)
    return "none", None


def _admission_priority(item: AuditInventoryItem) -> tuple[int, int, int, str]:
    return (
        0 if item.official_localization_verified else 1,
        item.structure_risk_score,
        -item.estimated_work_units,
        item.source_id,
    )


def _allocate_reviewer_product_targets(
    candidates_by_reviewer: Mapping[
        AssignedReviewer,
        Sequence[AuditInventoryItem],
    ],
    reviewer_capacities: Mapping[AssignedReviewer, int],
    manifest_product_counts: Mapping[Product, int],
) -> dict[AssignedReviewer, dict[Product, int]]:
    manifest_total = sum(manifest_product_counts.values())
    selected_total = sum(reviewer_capacities.values())
    if manifest_total < 1:
        message = "pilot selection requires a non-empty manifest"
        raise ValueError(message)
    options = tuple(
        _claude_quota_options(
            candidates_by_reviewer[reviewer],
            reviewer_capacities[reviewer],
        )
        for reviewer in _REVIEWERS
    )
    best_counts: tuple[int, ...] | None = None
    best_score: tuple[int, int, tuple[int, ...]] | None = None
    manifest_claude = manifest_product_counts["claude-code"]
    for counts in cartesian_product(*options):
        total_claude = sum(counts)
        overall_gap = abs(total_claude * manifest_total - selected_total * manifest_claude)
        reviewer_gap = sum(
            abs(count * manifest_total - reviewer_capacities[reviewer] * manifest_claude)
            for reviewer, count in zip(_REVIEWERS, counts, strict=True)
        )
        score = (overall_gap, reviewer_gap, counts)
        if best_score is None or score < best_score:
            best_score = score
            best_counts = counts
    if best_counts is None:
        message = "pilot product allocation has no feasible solution"
        raise ValueError(message)
    return {
        reviewer: {
            "claude-code": claude_count,
            "codex": reviewer_capacities[reviewer] - claude_count,
        }
        for reviewer, claude_count in zip(
            _REVIEWERS,
            best_counts,
            strict=True,
        )
    }


def _claude_quota_options(
    candidates: Sequence[AuditInventoryItem],
    capacity: int,
) -> range:
    available = {
        product: sum(item.product == product for item in candidates) for product in _PRODUCTS
    }
    minimum = max(0, capacity - available["codex"])
    maximum = min(capacity, available["claude-code"])
    if capacity >= _MIN_DIVERSE_CAPACITY and all(available[product] > 0 for product in _PRODUCTS):
        minimum = max(minimum, 1)
        maximum = min(maximum, capacity - 1)
    if minimum > maximum:
        message = "pilot reviewer capacity cannot be satisfied"
        raise ValueError(message)
    return range(minimum, maximum + 1)


def _select_reviewer_candidates(
    candidates: Sequence[AuditInventoryItem],
    product_targets: Mapping[Product, int],
) -> tuple[AuditInventoryItem, ...]:
    remaining = dict(product_targets)
    selected: list[AuditInventoryItem] = []
    pressure_candidates = tuple(item for item in candidates if remaining[item.product] > 0)
    if pressure_candidates:
        representative = min(
            pressure_candidates,
            key=lambda item: (
                -item.estimated_work_units,
                item.structure_risk_score,
                0 if item.official_localization_verified else 1,
                item.source_id,
            ),
        )
        selected.append(representative)
        remaining[representative.product] -= 1
    for product in _PRODUCTS:
        ranked = sorted(
            (item for item in candidates if item.product == product and item not in selected),
            key=_admission_priority,
        )
        selected.extend(ranked[: remaining[product]])
    expected = sum(product_targets.values())
    if len(selected) != expected:
        message = "pilot reviewer selection did not satisfy product targets"
        raise ValueError(message)
    return tuple(selected)


def _validate_pilot_products(batch: PilotBatch) -> None:
    expected_product_keys = set(_PRODUCTS)
    for values in (
        batch.manifest_product_counts,
        batch.product_targets,
        batch.product_counts,
    ):
        if set(values) != expected_product_keys:
            message = "pilot product counts must cover both products"
            raise ValueError(message)
    if sum(batch.product_targets.values()) != batch.selected_count:
        message = "pilot product targets do not match selected_count"
        raise ValueError(message)
    actual: dict[Product, int] = dict.fromkeys(_PRODUCTS, 0)
    for selection in batch.selections:
        actual[selection.product] += 1
    if batch.product_counts != actual:
        message = "pilot product_counts does not match selections"
        raise ValueError(message)
    if batch.product_targets != actual:
        message = "pilot selections do not satisfy product targets"
        raise ValueError(message)


def _reviewers_in_document(
    document: Mapping[str, object],
) -> tuple[AssignedReviewer, ...]:
    found: list[AssignedReviewer] = []
    for field in ("assigned_reviewer", "review_model"):
        value = document.get(field)
        if value == "gpt-5.6-terra":
            found.append("gpt-5.6-terra")
        elif value == "grok-4.5":
            found.append("grok-4.5")
    return _ordered_reviewers(found)


def _ordered_reviewers(
    reviewers: Iterable[AssignedReviewer],
) -> tuple[AssignedReviewer, ...]:
    unique = set(reviewers)
    return tuple(reviewer for reviewer in _REVIEWERS if reviewer in unique)


def _reviewer_rank(reviewer: AssignedReviewer) -> int:
    return _REVIEWERS.index(reviewer)


def _read_json_object(path: Path) -> dict[str, object] | None:
    try:
        value = cast(
            "object",
            json.loads(path.read_text(encoding="utf-8-sig")),
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(value, dict):
        return None
    untyped = cast("dict[object, object]", value)
    if not all(isinstance(key, str) for key in untyped):
        return None
    return {cast("str", key): item for key, item in untyped.items()}


def _empty_metrics() -> _MarkdownMetrics:
    return _MarkdownMetrics(
        characters=0,
        headings=0,
        fenced_blocks=0,
        links=0,
        mdx_tags=0,
    )


def _source_order_sha256(source_ids: Sequence[str]) -> str:
    return sha256_text("\n".join(source_ids))


def _repo_relative(root: Path, path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(root).as_posix()
    except ValueError as exc:
        message = "audit inventory path is outside the repository"
        raise ValueError(message) from exc


def _require_source_id(source_id: str) -> None:
    if _SOURCE_ID_RE.fullmatch(source_id) is None or ".." in source_id:
        message = "audit inventory source_id is unsafe"
        raise ValueError(message)


def _require_relative_inventory_path(value: str) -> str:
    if (
        not value
        or value.startswith("/")
        or "\\" in value
        or ":" in value
        or any(part in {"", ".", ".."} for part in value.split("/"))
    ):
        message = "audit inventory paths must be sanitized repository-relative paths"
        raise ValueError(message)
    return value
