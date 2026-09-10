# Copyright 2026

"""Internal command-line control plane for the reviewed-repair pipeline."""

from __future__ import annotations

import sys
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Final, cast

import typer

from scripts.ai.audit_admission import admit_audit_pilot
from scripts.ai.audit_bridge import bridge_and_queue_deep_audit
from scripts.ai.audit_inventory import (
    build_inventory,
    write_inventory_atomic,
)
from scripts.ai.audit_prepare import prepare_deep_audit_manifest
from scripts.ai.audit_worker import (
    finalize_assigned_audit_worker,
    prepare_assigned_audit_worker,
)
from scripts.ai.pipeline import PipelineStore, RepairJobSpec
from scripts.ai.pipeline_adapters import (
    attach_materialized_review,
    finalize_targeted_fix_worker,
    ingest_grok_final_review,
    ingest_targeted_fix,
    ingest_terra_final_review,
    prepare_targeted_fix_worker,
)
from scripts.ai.pipeline_control import (
    AdmissionControlPolicy,
    ContinuousAuditAdmissionController,
)
from scripts.ai.pipeline_dispatcher import (
    CompletionEnvelope,
    DispatchStage,
    PipelineDispatcher,
)
from scripts.ai.pipeline_intake import (
    AuditIntakeSpec,
    AuditIntakeStore,
)
from scripts.ai.pipeline_promotion import (
    CleanAdoptionBatchRunner,
    PromotionBatchRunner,
)
from scripts.ai.review_contract import (
    RepairReadyReviewDraft,
    load_repair_ready_review,
    materialize_repair_ready_review,
    write_repair_ready_review,
)

if TYPE_CHECKING:
    from pydantic import BaseModel

    from scripts.ai.audit_admission import ReviewWorkflowVersion
    from scripts.ai.pipeline import Provider, ProviderModel
    from scripts.ai.review_contract import AssignedReviewer

app = typer.Typer(
    help="Operate the local resumable translation-review pipeline.",
    no_args_is_help=True,
)

_DEFAULT_REPO_ROOT: Final = Path()
_DEFAULT_PIPELINE_ROOT: Final = Path(".ai-local/pipeline-v1")
_DEFAULT_INVENTORY_PATH: Final = Path(
    ".ai-local/pipeline-v1/audit-inventory.json"
)

RepoRoot = Annotated[
    Path,
    typer.Option(
        "--repo-root",
        exists=True,
        file_okay=False,
        resolve_path=True,
        help="LewisDocs repository root.",
    ),
]
PipelineRoot = Annotated[
    Path,
    typer.Option(
        "--pipeline-root",
        file_okay=False,
        resolve_path=True,
        help="Persistent pipeline state directory.",
    ),
]


class RepairFailureDisposition(StrEnum):
    """Operator decision for a failed repair attempt."""

    RETRYABLE = "retryable"
    TERMINAL = "terminal"


def _store(repo_root: Path, pipeline_root: Path) -> PipelineStore:
    """Build a store from explicit, side-effect-free local paths."""
    return PipelineStore(pipeline_root, repo_root)


def _intake_store(
    repo_root: Path,
    pipeline_root: Path,
) -> AuditIntakeStore:
    """Build the first-class audit intake over the canonical repair store."""
    return AuditIntakeStore(_store(repo_root, pipeline_root))


def _repo_relative(path: Path, repo_root: Path) -> str:
    """Return a normalized repository-relative artifact path."""
    resolved = path if path.is_absolute() else repo_root / path
    try:
        return resolved.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError as exc:
        message = "pipeline artifact path is outside the repository"
        raise ValueError(message) from exc


def _emit(value: BaseModel | tuple[BaseModel, ...]) -> None:
    """Write stable JSON to stdout for orchestration scripts."""
    if isinstance(value, tuple):
        rendered = "[" + ",".join(item.model_dump_json(indent=2) for item in value) + "]"
    else:
        rendered = value.model_dump_json(indent=2)
    _ = sys.stdout.write(rendered + "\n")


@app.command("status")
def status(
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """Show queue depths, active work, and review backpressure."""
    _emit(_store(repo_root, pipeline_root).status())


@app.command("metrics")
def metrics(
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """Show stage wall times derived from immutable transition events."""
    _emit(_store(repo_root, pipeline_root).metrics())


@app.command("intake-status")
def intake_status(
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """Show deep-audit, bridge, and combined downstream WIP."""
    _emit(_intake_store(repo_root, pipeline_root).status())


@app.command("intake-metrics")
def intake_metrics(
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """Show audit and bridge queue and service timings."""
    _emit(_intake_store(repo_root, pipeline_root).metrics())


@app.command("audit-inventory")
def audit_inventory(
    output_path: Annotated[
        Path,
        typer.Option("--output", dir_okay=False, resolve_path=True),
    ] = _DEFAULT_INVENTORY_PATH,
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """Build the conserved admission inventory without launching work."""
    intake = _intake_store(repo_root, pipeline_root)
    inventory = build_inventory(
        repo_root,
        pipeline_store=intake.store,
        intake_store=intake,
    )
    _ = write_inventory_atomic(output_path, inventory)
    _emit(inventory)


@app.command("admit-audit-pilot")
def admit_pilot(  # noqa: PLR0913, PLR0917
    batch_id: Annotated[str, typer.Option("--batch-id")],
    max_pages: Annotated[
        int,
        typer.Option("--max-pages", min=1, max=12),
    ] = 12,
    actor: Annotated[str, typer.Option("--actor")] = "audit-admission",
    review_workflow_version: Annotated[
        int,
        typer.Option("--review-workflow-version", min=2, max=3),
    ] = 3,
    excluded_source_ids: Annotated[
        list[str] | None,
        typer.Option(
            "--exclude-source-id",
            help="Explicit source id to keep out of this bounded pilot.",
        ),
    ] = None,
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """Atomically plan and admit one bounded deep-audit batch."""
    _emit(
        admit_audit_pilot(
            repo_root=repo_root,
            intake_store=_intake_store(repo_root, pipeline_root),
            batch_id=batch_id,
            max_pages=max_pages,
            actor=actor,
            review_workflow_version=cast(
                "ReviewWorkflowVersion",
                review_workflow_version,
            ),
            excluded_source_ids=excluded_source_ids or (),
        )
    )


@app.command("intake-list")
def intake_list(
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """List all immutable deep-audit intake snapshots."""
    _emit(_intake_store(repo_root, pipeline_root).list_items())


@app.command("intake-create")
def intake_create(
    spec_path: Annotated[
        Path,
        typer.Argument(exists=True, dir_okay=False, resolve_path=True),
    ],
    actor: Annotated[str, typer.Option("--actor")],
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """Reserve and queue one manifest-bound assigned deep audit."""
    spec = AuditIntakeSpec.model_validate_json(
        spec_path.read_text(encoding="utf-8-sig")
    )
    _emit(
        _intake_store(repo_root, pipeline_root).create(
            spec,
            actor=actor,
        )
    )


@app.command("prepare-audit-manifest")
def prepare_audit_manifest(
    source_ids: Annotated[
        list[str],
        typer.Option(
            "--source-id",
            help="Explicit source id; repeat for each mutually exclusive page.",
        ),
    ],
    output_path: Annotated[
        Path,
        typer.Option(
            "--output",
            dir_okay=False,
            help="Manifest path under .ai-local.",
        ),
    ],
    purpose: Annotated[
        str,
        typer.Option("--purpose", min=1),
    ] = "explicit-source-mutually-exclusive-deep-audit",
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """Prepare exact final-site-shape pairs before assigned deep audit."""
    _emit(
        prepare_deep_audit_manifest(
            repo_root=repo_root,
            output_path=output_path,
            source_ids=source_ids,
            intake_store=_intake_store(repo_root, pipeline_root),
            purpose=purpose,
        )
    )


@app.command("intake-complete-audit")
def intake_complete_audit(  # noqa: PLR0913, PLR0917
    intake_id: str,
    report_path: Annotated[
        Path,
        typer.Argument(exists=True, dir_okay=False, resolve_path=True),
    ],
    worker_id: Annotated[str, typer.Option("--worker")],
    duration_ms: Annotated[int, typer.Option("--duration-ms", min=0)],
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """Bind one completed assigned deep audit to its intake lease."""
    _emit(
        _intake_store(repo_root, pipeline_root).complete_audit(
            intake_id,
            worker_id,
            _repo_relative(report_path, repo_root),
            duration_ms=duration_ms,
        )
    )


@app.command("prepare-audit-worker")
def prepare_audit_worker(
    intake_id: str,
    worker_id: Annotated[str, typer.Option("--worker")],
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """Prepare the shared v2 prompt and schema for one claimed audit."""
    _emit(
        prepare_assigned_audit_worker(
            _intake_store(repo_root, pipeline_root),
            intake_id=intake_id,
            worker_id=worker_id,
        )
    )


@app.command("finalize-audit-worker")
def finalize_audit_worker(
    worker_manifest_path: Annotated[
        Path,
        typer.Argument(exists=True, dir_okay=False, resolve_path=True),
    ],
    duration_ms: Annotated[int, typer.Option("--duration-ms", min=0)],
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """Materialize compact findings and submit one validated audit completion."""
    _emit(
        finalize_assigned_audit_worker(
            _intake_store(repo_root, pipeline_root),
            worker_manifest_path=worker_manifest_path,
            duration_ms=duration_ms,
        )
    )


@app.command("intake-route")
def intake_route(
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """Route completed audits to bridge or clean-adoption queues."""
    _emit(
        _intake_store(repo_root, pipeline_root).route_completed_audits()
    )


@app.command("intake-heartbeat")
def intake_heartbeat(
    intake_id: str,
    worker_id: Annotated[str, typer.Option("--worker")],
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """Renew one active deep-audit or bridge lease."""
    _emit(
        _intake_store(repo_root, pipeline_root).heartbeat(
            intake_id,
            worker_id,
        )
    )


@app.command("intake-complete-bridge")
def intake_complete_bridge(
    intake_id: str,
    worker_id: Annotated[str, typer.Option("--worker")],
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """Create the stable exact-span repair after a claimed bridge."""
    _emit(
        _intake_store(repo_root, pipeline_root).complete_bridge(
            intake_id,
            worker_id,
        )
    )


@app.command("list")
def list_jobs(
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """List the latest materialized snapshot for every repair attempt."""
    _emit(_store(repo_root, pipeline_root).list_jobs())


@app.command("create")
def create(
    spec_path: Annotated[
        Path,
        typer.Argument(exists=True, dir_okay=False, resolve_path=True),
    ],
    actor: Annotated[str, typer.Option("--actor")],
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """Validate a repair-ready review and queue one immutable attempt."""
    spec = RepairJobSpec.model_validate_json(spec_path.read_text(encoding="utf-8-sig"))
    _emit(_store(repo_root, pipeline_root).create_job(spec, actor=actor))


@app.command("queue")
def queue(  # noqa: PLR0913, PLR0917
    review_path: Annotated[
        Path,
        typer.Argument(exists=True, dir_okay=False, resolve_path=True),
    ],
    provider_value: Annotated[str, typer.Option("--provider")],
    attempt_id: Annotated[str, typer.Option("--attempt-id")],
    actor: Annotated[str, typer.Option("--actor")],
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """Derive an immutable job spec from a validated repair-ready review."""
    if provider_value not in {"kimi", "glm"}:
        message = "provider must be kimi or glm"
        raise typer.BadParameter(message, param_hint="--provider")
    provider = cast("Provider", provider_value)
    model: ProviderModel = "k3" if provider == "kimi" else "glm-5.2"
    review = load_repair_ready_review(review_path, repo_root)
    spec = RepairJobSpec(
        source_id=review.source_id,
        source_path=review.source_path,
        candidate_path=review.candidate_path,
        source_sha256=review.source_sha256,
        base_candidate_sha256=review.candidate_sha256,
        review_path=_repo_relative(review_path, repo_root),
        assigned_reviewer=review.assigned_reviewer,
        provider=provider,
        provider_model=model,
        attempt_id=attempt_id,
    )
    _emit(_store(repo_root, pipeline_root).create_job(spec, actor=actor))


@app.command("bridge")
def bridge(
    draft_path: Annotated[
        Path,
        typer.Argument(exists=True, dir_okay=False, resolve_path=True),
    ],
    output_path: Annotated[Path, typer.Argument(resolve_path=True)],
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
) -> None:
    """Convert reviewed exact spans into a validated repair-ready report."""
    draft = RepairReadyReviewDraft.model_validate_json(
        draft_path.read_text(encoding="utf-8-sig")
    )
    review = materialize_repair_ready_review(draft, repo_root)
    write_repair_ready_review(output_path, review)
    _emit(review)


@app.command("ingest-deep-audit")
def ingest_deep_audit(  # noqa: PLR0913, PLR0917
    manifest_path: Annotated[
        Path,
        typer.Argument(exists=True, dir_okay=False, resolve_path=True),
    ],
    report_path: Annotated[
        Path,
        typer.Argument(exists=True, dir_okay=False, resolve_path=True),
    ],
    repair_review_path: Annotated[
        Path,
        typer.Argument(resolve_path=True),
    ],
    source_id: Annotated[str, typer.Option("--source-id")],
    reviewer_value: Annotated[str, typer.Option("--reviewer")],
    provider_value: Annotated[str, typer.Option("--provider")],
    attempt_id: Annotated[str, typer.Option("--attempt-id")],
    actor: Annotated[str, typer.Option("--actor")],
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """Validate one deep audit, bridge exact spans, and queue its repair."""
    if reviewer_value not in {"gpt-5.6-terra", "grok-4.5"}:
        message = "reviewer must be gpt-5.6-terra or grok-4.5"
        raise typer.BadParameter(message, param_hint="--reviewer")
    if provider_value not in {"kimi", "glm"}:
        message = "provider must be kimi or glm"
        raise typer.BadParameter(message, param_hint="--provider")
    reviewer = cast("AssignedReviewer", reviewer_value)
    provider = cast("Provider", provider_value)
    _emit(
        bridge_and_queue_deep_audit(
            store=_store(repo_root, pipeline_root),
            manifest_path=manifest_path,
            report_path=report_path,
            repair_review_path=repair_review_path,
            source_id=source_id,
            assigned_reviewer=reviewer,
            provider=provider,
            attempt_id=attempt_id,
            actor=actor,
        )
    )


@app.command("claim-repair")
def claim_repair(
    job_id: str,
    worker_id: Annotated[str, typer.Option("--worker")],
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """Claim one provider-specific repair lease."""
    _emit(_store(repo_root, pipeline_root).claim_repair(job_id, worker_id))


@app.command("complete-repair")
def complete_repair(
    job_id: str,
    result_path: Path,
    worker_id: Annotated[str, typer.Option("--worker")],
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """Record a locally validated provider result and queue assigned review."""
    _emit(
        _store(repo_root, pipeline_root).complete_repair(
            job_id,
            worker_id,
            _repo_relative(result_path, repo_root),
        )
    )


@app.command("prepare-repair-worker")
def prepare_repair_worker(
    job_id: str,
    worker_id: Annotated[str, typer.Option("--worker")],
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """Prepare a deterministic targeted-runner manifest for a claimed repair."""
    _emit(
        prepare_targeted_fix_worker(
            _store(repo_root, pipeline_root),
            job_id=job_id,
            worker_id=worker_id,
        )
    )


@app.command("fail-repair")
def fail_repair(  # noqa: PLR0913, PLR0917
    job_id: str,
    reason: Annotated[str, typer.Option("--reason", min=1, max=500)],
    worker_id: Annotated[str, typer.Option("--worker")],
    disposition: Annotated[
        RepairFailureDisposition,
        typer.Option(
            "--disposition",
            help="Choose retryable or terminal; terminal is the safe default.",
        ),
    ] = RepairFailureDisposition.TERMINAL,
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """Record a repair failure, release its lease, and stop automatic retries."""
    _emit(
        _store(repo_root, pipeline_root).fail_repair(
            job_id,
            worker_id,
            reason=reason,
            retryable=disposition == RepairFailureDisposition.RETRYABLE,
        )
    )


@app.command("retry-repair")
def retry_repair(
    job_id: str,
    actor: Annotated[str, typer.Option("--actor")],
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """Explicitly requeue one retryable repair after its cause is understood."""
    _emit(
        _store(repo_root, pipeline_root).requeue_failed_repair(
            job_id,
            actor=actor,
        )
    )


@app.command("ingest-repair")
def ingest_repair(  # noqa: PLR0913, PLR0917
    job_id: str,
    artifact_path: Path,
    materialized_manifest_path: Path,
    worker_id: Annotated[str, typer.Option("--worker")],
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """Validate a targeted-fix artifact and complete its repair lease."""
    _emit(
        ingest_targeted_fix(
            _store(repo_root, pipeline_root),
            job_id=job_id,
            worker_id=worker_id,
            artifact_path_value=_repo_relative(artifact_path, repo_root),
            materialized_manifest_path_value=_repo_relative(
                materialized_manifest_path,
                repo_root,
            ),
        )
    )


@app.command("finalize-repair-worker")
def finalize_repair_worker(
    job_id: str,
    artifact_path: Path,
    worker_id: Annotated[str, typer.Option("--worker")],
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """Materialize, validate, and ingest one completed targeted repair."""
    _emit(
        finalize_targeted_fix_worker(
            _store(repo_root, pipeline_root),
            job_id=job_id,
            worker_id=worker_id,
            artifact_path_value=_repo_relative(artifact_path, repo_root),
        )
    )


@app.command("attach-review")
def attach_review(
    job_id: str,
    materialized_manifest_path: Path,
    actor: Annotated[str, typer.Option("--actor")],
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """Attach a verified final-site-shape pair to an existing repair candidate."""
    _emit(
        attach_materialized_review(
            _store(repo_root, pipeline_root),
            job_id=job_id,
            materialized_manifest_path_value=_repo_relative(
                materialized_manifest_path,
                repo_root,
            ),
            actor=actor,
        )
    )


@app.command("enqueue-reviews")
def enqueue_reviews(
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """Fill available review queue capacity from validated candidates."""
    _emit(_store(repo_root, pipeline_root).enqueue_waiting_reviews())


@app.command("claim-review")
def claim_review(
    job_id: str,
    worker_id: Annotated[str, typer.Option("--worker")],
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """Claim one final-review lease for its original assigned reviewer."""
    _emit(_store(repo_root, pipeline_root).claim_review(job_id, worker_id))


@app.command("complete-review")
def complete_review(
    job_id: str,
    review_path: Path,
    worker_id: Annotated[str, typer.Option("--worker")],
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """Record the assigned full-page verdict and route the candidate."""
    _emit(
        _store(repo_root, pipeline_root).complete_review(
            job_id,
            worker_id,
            _repo_relative(review_path, repo_root),
        )
    )


@app.command("ingest-grok-review")
def ingest_grok_review(  # noqa: PLR0913, PLR0917
    job_id: str,
    report_path: Path,
    status_path: Path,
    worker_id: Annotated[str, typer.Option("--worker")],
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """Validate and record one assigned Grok full-page review."""
    _emit(
        ingest_grok_final_review(
            _store(repo_root, pipeline_root),
            job_id=job_id,
            worker_id=worker_id,
            report_path_value=_repo_relative(report_path, repo_root),
            status_path_value=_repo_relative(status_path, repo_root),
        )
    )


@app.command("ingest-terra-review")
def ingest_terra_review(  # noqa: PLR0913, PLR0917
    job_id: str,
    report_path: Path,
    worker_id: Annotated[str, typer.Option("--worker")],
    invalid_attempt_count: Annotated[
        int,
        typer.Option("--invalid-attempt-count", min=0),
    ] = 0,
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """Validate and record one assigned Terra full-page review."""
    _emit(
        ingest_terra_final_review(
            _store(repo_root, pipeline_root),
            job_id=job_id,
            worker_id=worker_id,
            report_path_value=_repo_relative(report_path, repo_root),
            invalid_attempt_count=invalid_attempt_count,
        )
    )


@app.command("promote")
def promote(
    job_id: str,
    evidence_path: Path,
    actor: Annotated[str, typer.Option("--actor")],
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """Record promotion only after every final site gate passes."""
    _emit(
        _store(repo_root, pipeline_root).promote(
            job_id,
            _repo_relative(evidence_path, repo_root),
            actor=actor,
        )
    )


@app.command("heartbeat")
def heartbeat(
    job_id: str,
    worker_id: Annotated[str, typer.Option("--worker")],
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """Renew an active repair or review lease."""
    _emit(_store(repo_root, pipeline_root).heartbeat(job_id, worker_id))


@app.command("recover")
def recover(
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """Return jobs with expired worker leases to their prior queues."""
    _emit(_store(repo_root, pipeline_root).recover_expired_leases())


@app.command("dispatch-once")
def dispatch_once(
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """Absorb completed work and publish one deduplicated action snapshot."""
    dispatcher = PipelineDispatcher(_store(repo_root, pipeline_root))
    _emit(dispatcher.reconcile())


@app.command("admission-control")
def admission_control(
    batch_prefix: Annotated[
        str,
        typer.Option("--batch-prefix"),
    ] = "deep-audit-v3-flow",
    review_workflow_version: Annotated[
        int,
        typer.Option("--review-workflow-version", min=2, max=3),
    ] = 3,
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """Run one quality-gated continuous deep-audit admission cycle."""
    store = _store(repo_root, pipeline_root)
    policy = AdmissionControlPolicy(
        batch_prefix=batch_prefix,
        review_workflow_version=cast(
            "ReviewWorkflowVersion",
            review_workflow_version,
        ),
    )
    _emit(ContinuousAuditAdmissionController(store, policy=policy).tick())


@app.command("submit-completion")
def submit_completion(
    envelope_path: Annotated[
        Path,
        typer.Argument(exists=True, dir_okay=False, resolve_path=True),
    ],
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """Atomically place one validated external completion in the inbox."""
    envelope = CompletionEnvelope.model_validate_json(
        envelope_path.read_text(encoding="utf-8-sig")
    )
    dispatcher = PipelineDispatcher(_store(repo_root, pipeline_root))
    _emit(dispatcher.submit_completion(envelope))


@app.command("dispatch-run")
def dispatch_run(  # noqa: PLR0913
    *,
    auto_bridge: Annotated[
        bool,
        typer.Option(
            "--auto-bridge",
            help=(
                "Continuously validate completed deep audits and queue their "
                "exact-span repairs without a model call."
            ),
        ),
    ] = False,
    auto_admit: Annotated[
        bool,
        typer.Option(
            "--auto-admit",
            help=(
                "Continuously admit bounded deep-audit batches while quality "
                "and downstream WIP gates remain green."
            ),
        ),
    ] = False,
    auto_promote: Annotated[
        bool,
        typer.Option(
            "--auto-promote",
            help=(
                "Run complete small-batch site gates whenever the dispatcher "
                "reaches the size or wait threshold."
            ),
        ),
    ] = False,
    review_only_audit: Annotated[
        bool,
        typer.Option(
            "--review-only-audit",
            help=(
                "Ingest deep-audit completions without routing them to "
                "bridge, repair, clean adoption, or promotion."
            ),
        ),
    ] = False,
    poll_seconds: Annotated[
        float,
        typer.Option("--poll-seconds", min=0.1, max=60),
    ] = 2.0,
    max_cycles: Annotated[
        int,
        typer.Option(
            "--max-cycles",
            min=0,
            help="Zero keeps the reconciler running until interrupted.",
        ),
    ] = 0,
    admission_batch_prefix: Annotated[
        str,
        typer.Option("--admission-batch-prefix"),
    ] = "deep-audit-v3-flow",
    review_workflow_version: Annotated[
        int,
        typer.Option("--review-workflow-version", min=2, max=3),
    ] = 3,
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """Continuously reconcile queues and optionally consume due promotions."""
    store = _store(repo_root, pipeline_root)
    dispatcher = PipelineDispatcher(store)
    admission_controller = ContinuousAuditAdmissionController(
        store,
        policy=AdmissionControlPolicy(
            batch_prefix=admission_batch_prefix,
            review_workflow_version=cast(
                "ReviewWorkflowVersion",
                review_workflow_version,
            ),
        ),
    )
    promotion_runner = PromotionBatchRunner(store)
    clean_adoption_runner = CleanAdoptionBatchRunner(store)

    def consume_due_promotions() -> object:
        _ = promotion_runner.run_due()
        return clean_adoption_runner.run_due()

    with store.coordinator_lock("dispatcher-run"):
        _emit(
            dispatcher.run(
                poll_seconds=poll_seconds,
                max_cycles=None if max_cycles == 0 else max_cycles,
                on_admission_cycle=(
                    admission_controller.tick if auto_admit else None
                ),
                on_promotion_due=(
                    consume_due_promotions if auto_promote else None
                ),
                auto_bridge=auto_bridge,
                review_only_audit=review_only_audit,
            )
        )


@app.command("claim-next")
def claim_next(
    stage: DispatchStage,
    lane: Annotated[str, typer.Option("--lane")],
    worker_id: Annotated[str, typer.Option("--worker")],
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """Claim the oldest compatible deduplicated repair or review action."""
    dispatcher = PipelineDispatcher(_store(repo_root, pipeline_root))
    _emit(dispatcher.claim_next(stage, lane, worker_id))


@app.command("promote-due")
def promote_due(
    *,
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            help="Run the small batch even before size or age thresholds.",
        ),
    ] = False,
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """Run one transactional small-batch promotion with complete site gates."""
    store = _store(repo_root, pipeline_root)
    _emit(PromotionBatchRunner(store).run_due(force=force))


@app.command("adopt-clean-due")
def adopt_clean_due(
    *,
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            help="Run the clean adoption batch before size or age thresholds.",
        ),
    ] = False,
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """Transactionally adopt assigned-review pass pages without repair."""
    store = _store(repo_root, pipeline_root)
    _emit(CleanAdoptionBatchRunner(store).run_due(force=force))


@app.command("events")
def events(
    job_id: str,
    repo_root: RepoRoot = _DEFAULT_REPO_ROOT,
    pipeline_root: PipelineRoot = _DEFAULT_PIPELINE_ROOT,
) -> None:
    """Show the immutable event history for one attempt."""
    _emit(_store(repo_root, pipeline_root).events(job_id))


def main() -> None:
    """Run the internal pipeline control plane."""
    command = typer.main.get_command(app)
    command(prog_name="scripts.ai.pipeline_cli")


if __name__ == "__main__":
    raise SystemExit(main())
