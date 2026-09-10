# Copyright 2026

"""Prepare explicit source ids for mutually exclusive deep review."""

from __future__ import annotations

import re
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final, Literal

from scripts.ai.audit_bridge import (
    DeepAuditManifest,
    DeepAuditManifestEntry,
)
from scripts.ai.audit_context import build_audit_v3_context
from scripts.ai.audit_coverage import derive_coverage_contract
from scripts.ai.audit_history import recover_audit_history
from scripts.ai.audit_preflight import inspect_audit_preflight_pair
from scripts.ai.final_shape import (
    require_final_shape_pair,
    write_final_shape_evidence,
)
from scripts.ai.materialize import derive_review_pair
from scripts.ai.page_format import AcceptedPage, parse_accepted_page
from scripts.ai.protect import restore_fenced_blocks
from scripts.ai.review_contract import sha256_bytes, sha256_path
from scripts.ai.types import SourceId

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from scripts.ai.audit_coverage import DeepAuditCoverageContract
    from scripts.ai.pipeline_intake import AuditIntakeStore
    from scripts.ai.review_contract import AssignedReviewer

_PURPOSE: Final = "explicit-source-mutually-exclusive-deep-audit"
_SOURCE_ID_RE: Final = re.compile(
    r"^(?:claude-code|codex)/[a-z0-9][a-z0-9/-]*$"
)
_REVIEW_WORKFLOW_V3: Final = 3


@dataclass(frozen=True)
class _ReviewWorkflow:
    """Reviewer ownership fixed before evidence preparation."""

    version: Literal[2, 3]
    assigned_reviewer: AssignedReviewer | None


@dataclass(frozen=True)
class _V3ArtifactInput:
    """Paths and immutable contract needed for v3 evidence artifacts."""

    root: Path
    artifact_root: Path
    staged_root: Path
    staged_english: Path
    staged_chinese: Path
    english_path: Path
    chinese_path: Path
    coverage_contract: DeepAuditCoverageContract
    assigned_reviewer: AssignedReviewer


@dataclass(frozen=True)
class _NormalizedCandidate:
    """Candidate bytes and optional immutable v3 staging pair."""

    path: Path
    content: bytes
    fenced_blocks_restored: int
    staged_pair: tuple[Path, Path] | None


@dataclass(frozen=True)
class _NormalizeInput:
    """Inputs for preparing one immutable v3 candidate."""

    root: Path
    artifact_root: Path
    staged_root: Path
    source_id: str
    source_path: Path
    candidate_path: Path
    workflow: _ReviewWorkflow


def prepare_deep_audit_manifest(  # noqa: PLR0913
    *,
    repo_root: Path,
    output_path: Path,
    source_ids: Iterable[str],
    intake_store: AuditIntakeStore,
    purpose: str = _PURPOSE,
    review_workflow_version: Literal[2, 3] = 2,
    assigned_reviewers: Mapping[str, AssignedReviewer] | None = None,
    candidate_paths: Mapping[str, Path] | None = None,
    artifact_root: Path | None = None,
) -> DeepAuditManifest:
    """Materialize hash-bound review pairs for explicit source ids."""
    root = repo_root.resolve()
    output = _inside(root, output_path)
    _require_local_output(root, output)
    requested = tuple(source_ids)
    if not requested:
        message = "at least one source_id is required"
        raise ValueError(message)
    if len(requested) != len(set(requested)):
        message = "deep-audit source_ids must be unique"
        raise ValueError(message)
    if review_workflow_version == _REVIEW_WORKFLOW_V3:
        reviewer_ids = set(assigned_reviewers or {})
        if reviewer_ids != set(requested):
            message = "v3 deep audit requires one assigned reviewer per source_id"
            raise ValueError(message)
    if candidate_paths is not None and set(candidate_paths) != set(requested):
        message = "candidate path overrides must match requested source_ids"
        raise ValueError(message)

    resolved_artifact_root = (
        root / ".ai-local"
        if artifact_root is None
        else _inside(root, artifact_root)
    )
    _require_local_output(root, resolved_artifact_root)

    local_root = root / ".ai-local"
    local_root.mkdir(parents=True, exist_ok=True)
    prepared: list[DeepAuditManifestEntry] = []
    with tempfile.TemporaryDirectory(
        prefix="audit-prepare-",
        dir=local_root,
    ) as temporary_value:
        temporary_root = Path(temporary_value)
        staged: list[tuple[Path, Path]] = []
        for source_id in requested:
            entry, staged_paths = _prepare_entry(
                root=root,
                temporary_root=temporary_root,
                source_id=source_id,
                intake_store=intake_store,
                candidate_path=(
                    None
                    if candidate_paths is None
                    else _inside(root, candidate_paths[source_id])
                ),
                artifact_root=resolved_artifact_root,
                workflow=_ReviewWorkflow(
                    version=review_workflow_version,
                    assigned_reviewer=(
                        assigned_reviewers[source_id]
                        if assigned_reviewers is not None
                        else None
                    ),
                ),
            )
            prepared.append(entry)
            staged.extend(staged_paths)

        for staged_path, destination_path in staged:
            _atomic_bytes(destination_path, staged_path.read_bytes())

    manifest = DeepAuditManifest(
        purpose=purpose,
        entries=tuple(entry.model_dump(mode="python") for entry in prepared),
    )
    _atomic_bytes(
        output,
        (manifest.model_dump_json(indent=2) + "\n").encode("utf-8"),
    )
    return manifest


def _prepare_entry(  # noqa: PLR0913
    *,
    root: Path,
    temporary_root: Path,
    source_id: str,
    intake_store: AuditIntakeStore,
    candidate_path: Path | None,
    artifact_root: Path,
    workflow: _ReviewWorkflow,
) -> tuple[DeepAuditManifestEntry, tuple[tuple[Path, Path], ...]]:
    _require_source_id(source_id)
    _require_unclaimed(intake_store, source_id)

    raw_source = _source_path(root, "en", source_id)
    raw_candidate = (
        candidate_path
        if candidate_path is not None
        else (
            root
            / ".ai-local"
            / "staging"
            / "dual-review-normalized"
            / f"{source_id}.md"
        )
    )
    formal_target = _source_path(root, "zh-CN", source_id)
    if formal_target.exists():
        message = f"formal Chinese target already exists: {source_id}"
        raise ValueError(message)
    if not raw_source.is_file() or not raw_candidate.is_file():
        message = f"deep-audit source pair is incomplete: {source_id}"
        raise ValueError(message)

    source_page = parse_accepted_page(raw_source)
    candidate_page = parse_accepted_page(raw_candidate)
    _validate_page_pair(source_id, source_page, candidate_page)

    staged_root = temporary_root / source_id
    normalized = _prepare_normalized_candidate(
        _NormalizeInput(
            root=root,
            artifact_root=artifact_root,
            staged_root=staged_root,
            source_id=source_id,
            source_path=raw_source,
            candidate_path=raw_candidate,
            workflow=workflow,
        )
    )
    staged_pairs = (
        [normalized.staged_pair]
        if normalized.staged_pair is not None
        else []
    )

    public_english, public_chinese = derive_review_pair(
        SourceId(source_id),
        raw_source.read_bytes(),
        normalized.content,
    )
    staged_english = staged_root / "en.md"
    staged_chinese = staged_root / "zh-CN.md"
    _atomic_bytes(staged_english, public_english)
    _atomic_bytes(staged_chinese, public_chinese)

    english_path = artifact_root / "audit-materialized" / source_id / "en.md"
    chinese_path = (
        artifact_root / "audit-materialized" / source_id / "zh-CN.md"
    )
    evidence = require_final_shape_pair(
        source_id,
        staged_english,
        staged_chinese,
        source_path_value=_relative(root, english_path),
        candidate_path_value=_relative(root, chinese_path),
    )
    staged_evidence = staged_root / "final-shape.json"
    write_final_shape_evidence(staged_evidence, evidence)
    evidence_path = artifact_root / "final-shape-evidence" / f"{source_id}.json"
    translation_model = candidate_page.translation_model
    if translation_model not in {"k3", "glm-5.2", "gpt-5.6"}:
        message = f"deep-audit candidate has unsupported provenance: {source_id}"
        raise ValueError(message)
    english_path_value = _relative(root, english_path)
    chinese_path_value = _relative(root, chinese_path)
    coverage_contract = derive_coverage_contract(
        source_id=source_id,
        english_path=staged_english,
        chinese_path=staged_chinese,
        english_path_value=english_path_value,
        chinese_path_value=chinese_path_value,
    )
    entry_values: dict[str, object] = {
        "audit_contract_version": 2,
        "review_workflow_version": workflow.version,
        "source_id": source_id,
        "status": "prepared",
        "english_path": english_path_value,
        "chinese_path": chinese_path_value,
        "normalized_candidate_path": _relative(root, normalized.path),
        "producer": f"{translation_model}+explicit-final-shape",
        "translation_model": translation_model,
        "source_sha256": sha256_path(staged_english),
        "candidate_sha256": sha256_path(staged_chinese),
        "normalized_candidate_sha256": sha256_bytes(
            normalized.content
        ),
        "fenced_blocks_restored": normalized.fenced_blocks_restored,
        "coverage_contract": coverage_contract,
    }
    staged_pairs.extend(
        (
            (staged_english, english_path),
            (staged_chinese, chinese_path),
            (staged_evidence, evidence_path),
        )
    )
    if workflow.version == _REVIEW_WORKFLOW_V3:
        if workflow.assigned_reviewer is None:
            message = f"v3 deep audit has no assigned reviewer: {source_id}"
            raise ValueError(message)
        artifact_fields, artifact_pairs = _prepare_v3_artifacts(
            _V3ArtifactInput(
                root=root,
                artifact_root=artifact_root,
                staged_root=staged_root,
                staged_english=staged_english,
                staged_chinese=staged_chinese,
                english_path=english_path,
                chinese_path=chinese_path,
                coverage_contract=coverage_contract,
                assigned_reviewer=workflow.assigned_reviewer,
            )
        )
        entry_values.update(artifact_fields)
        staged_pairs.extend(artifact_pairs)
    entry = DeepAuditManifestEntry.model_validate(entry_values)
    return entry, tuple(staged_pairs)


def _prepare_normalized_candidate(
    value: _NormalizeInput,
) -> _NormalizedCandidate:
    candidate_bytes = value.candidate_path.read_bytes()
    if value.workflow.version != _REVIEW_WORKFLOW_V3:
        return _NormalizedCandidate(
            path=value.candidate_path,
            content=candidate_bytes,
            fenced_blocks_restored=0,
            staged_pair=None,
        )

    restoration = restore_fenced_blocks(
        value.source_path.read_bytes().decode("utf-8-sig"),
        candidate_bytes.decode("utf-8-sig"),
    )
    normalized_bytes = restoration.text.encode("utf-8")
    normalized_sha256 = sha256_bytes(normalized_bytes)
    normalized_path = (
        value.artifact_root
        / "audit-normalized-v3"
        / value.source_id
        / f"{normalized_sha256}.md"
    )
    staged_normalized = value.staged_root / "normalized-v3.md"
    _atomic_bytes(staged_normalized, normalized_bytes)
    return _NormalizedCandidate(
        path=normalized_path,
        content=normalized_bytes,
        fenced_blocks_restored=restoration.changed_count,
        staged_pair=(staged_normalized, normalized_path),
    )


def _require_unclaimed(
    intake_store: AuditIntakeStore,
    source_id: str,
) -> None:
    store = intake_store.store
    if store.source_reservation(source_id) is not None:
        message = f"source already has an active intake: {source_id}"
        raise ValueError(message)
    if any(job.source_id == source_id for job in store.list_jobs()):
        message = f"source already has a canonical repair attempt: {source_id}"
        raise ValueError(message)
    if any(item.source_id == source_id for item in intake_store.list_items()):
        message = f"source already has a canonical audit intake: {source_id}"
        raise ValueError(message)


def _prepare_v3_artifacts(
    value: _V3ArtifactInput,
) -> tuple[dict[str, object], tuple[tuple[Path, Path], ...]]:
    contract = value.coverage_contract
    preflight = inspect_audit_preflight_pair(
        contract.source_id,
        value.staged_english,
        value.staged_chinese,
        source_path_value=contract.english_path,
        candidate_path_value=contract.chinese_path,
    )
    history = recover_audit_history(
        repo_root=value.root,
        source_id=contract.source_id,
        assigned_reviewer=value.assigned_reviewer,
        english_path=value.english_path,
        english_text=value.staged_english.read_text(encoding="utf-8"),
        chinese_path=value.chinese_path,
        chinese_text=value.staged_chinese.read_text(encoding="utf-8"),
        history_root=value.root / ".ai-local" / "reviews",
        include_low=True,
    )
    context = build_audit_v3_context(
        contract=contract,
        assigned_reviewer=value.assigned_reviewer,
        preflight=preflight,
        history=history,
    )
    artifact_root = (
        value.artifact_root
        / "audit-v3-context"
        / contract.source_id
        / context.candidate_sha256[:16]
    )
    staged_artifact_root = value.staged_root / "v3"
    artifacts = (
        ("preflight", preflight.model_dump_json(indent=2)),
        ("history", history.model_dump_json(indent=2)),
        ("context", context.model_dump_json(indent=2)),
        (
            "plan",
            context.plan.model_dump_json(indent=2, by_alias=True),
        ),
    )
    fields: dict[str, object] = {}
    pairs: list[tuple[Path, Path]] = []
    for name, content in artifacts:
        staged_artifact = staged_artifact_root / f"{name}.json"
        destination = artifact_root / f"{name}.json"
        _atomic_bytes(staged_artifact, (content + "\n").encode("utf-8"))
        pairs.append((staged_artifact, destination))
        field_prefix = "v3_context" if name == "context" else name
        if name == "plan":
            field_prefix = "v3_plan"
        fields[f"{field_prefix}_path"] = _relative(
            value.root,
            destination,
        )
        fields[f"{field_prefix}_sha256"] = sha256_path(staged_artifact)
    return fields, tuple(pairs)


def _validate_page_pair(
    source_id: str,
    source: AcceptedPage,
    candidate: AcceptedPage,
) -> None:
    if str(source.source_id) != source_id or source.lang != "en":
        message = f"invalid English source metadata: {source_id}"
        raise ValueError(message)
    if (
        str(candidate.source_id) != source_id
        or str(candidate.translation_of) != source_id
        or candidate.lang != "zh-CN"
        or candidate.content_sha256 != source.content_sha256
    ):
        message = f"invalid Chinese candidate metadata: {source_id}"
        raise ValueError(message)


def _require_source_id(source_id: str) -> None:
    if _SOURCE_ID_RE.fullmatch(source_id) is None or ".." in source_id:
        message = f"unsafe deep-audit source_id: {source_id}"
        raise ValueError(message)


def _source_path(root: Path, lang: str, source_id: str) -> Path:
    return root / "source-ai" / "content" / lang / f"{source_id}.md"


def _inside(root: Path, path: Path) -> Path:
    resolved = (path if path.is_absolute() else root / path).resolve()
    try:
        _ = resolved.relative_to(root)
    except ValueError as exc:
        message = "deep-audit path is outside the repository"
        raise ValueError(message) from exc
    return resolved


def _require_local_output(root: Path, output: Path) -> None:
    try:
        _ = output.relative_to(root / ".ai-local")
    except ValueError as exc:
        message = "deep-audit manifest must be written under .ai-local"
        raise ValueError(message) from exc


def _relative(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def _atomic_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        _ = temporary.write_bytes(data)
        _ = temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
