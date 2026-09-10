# Copyright 2026
# ruff: noqa: INP001, S101

"""Tests for first-class deep-audit and bridge pipeline intake."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, cast

import pytest

from scripts.ai.audit_bridge import bridge_deep_audit_report
from scripts.ai.pipeline import (
    PipelinePolicy,
    PipelineState,
    PipelineStore,
    RepairJobSpec,
)
from scripts.ai.pipeline_dispatcher import (
    CompletionEnvelope,
    CompletionKind,
    DispatchStage,
    PipelineDispatcher,
)
from scripts.ai.pipeline_intake import (
    AuditIntakeEventKind,
    AuditIntakeItem,
    AuditIntakeSpec,
    AuditIntakeState,
    AuditIntakeStore,
)
from scripts.ai.pipeline_promotion import (
    CleanAdoptionBatchRunner,
    CleanAdoptionTransaction,
    SiteGateResult,
)
from scripts.ai.review_contract import (
    sha256_path,
    write_repair_ready_review,
)

if TYPE_CHECKING:
    from pathlib import Path

AUDIT_DURATION_MS = 1200
BRIDGE_DURATION_MS = 800


def _write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(value, encoding="utf-8", newline="\n")


def _fixture(
    tmp_path: Path,
    *,
    verdict: str = "fail",
) -> tuple[Path, Path]:
    source_id = "codex/intake-test"
    raw_source = tmp_path / "source-ai/content/en/codex/intake-test.md"
    raw_candidate = (
        tmp_path
        / ".ai-local/staging/dual-review-normalized/codex/intake-test.md"
    )
    public_source = (
        tmp_path / ".ai-local/audit-materialized/codex/intake-test/en.md"
    )
    public_candidate = (
        tmp_path
        / ".ai-local/audit-materialized/codex/intake-test/zh-CN.md"
    )
    source_text = "# Settings\n\nThe client loads the settings file.\n"
    candidate_text = (
        "---\n"
        "title: Settings\n"
        "---\n\n"
        "# Settings\n\n"
        "This is the wrong translated sentence.\n"
    )
    _write(raw_source, source_text)
    _write(raw_candidate, candidate_text)
    _write(public_source, source_text)
    _write(public_candidate, candidate_text)

    manifest_path = tmp_path / ".ai-local/audit-intake-manifest.json"
    manifest = {
        "version": 1,
        "purpose": "pipeline-intake-test",
        "entries": [
            {
                "source_id": source_id,
                "status": "prepared",
                "english_path": public_source.relative_to(
                    tmp_path
                ).as_posix(),
                "chinese_path": public_candidate.relative_to(
                    tmp_path
                ).as_posix(),
                "normalized_candidate_path": raw_candidate.relative_to(
                    tmp_path
                ).as_posix(),
                "producer": "test",
                "translation_model": "glm-5.2",
                "source_sha256": sha256_path(public_source),
                "candidate_sha256": sha256_path(public_candidate),
                "normalized_candidate_sha256": sha256_path(raw_candidate),
                "fenced_blocks_restored": 0,
                "source_shard": 2,
                "source_entry_index": 17,
            }
        ],
    }
    _write(manifest_path, json.dumps(manifest, indent=2))

    report_path = tmp_path / ".ai-local/reviews/intake/report.json"
    report = {
        "source_id": source_id,
        "english_path": public_source.relative_to(tmp_path).as_posix(),
        "chinese_path": public_candidate.relative_to(tmp_path).as_posix(),
        "expected_source_sha256": sha256_path(public_source),
        "actual_source_sha256": sha256_path(public_source),
        "expected_candidate_sha256": sha256_path(public_candidate),
        "actual_candidate_sha256": sha256_path(public_candidate),
        "review_model": "gpt-5.6-terra",
        "verdict": verdict,
        "issues": (
            []
            if verdict == "pass"
            else [
                {
                    "severity": "high",
                    "category": "semantic_scope",
                    "location": "opening paragraph",
                    "source_excerpt": (
                        "The client loads the settings file."
                    ),
                    "candidate_span_text": (
                        "This is the wrong translated sentence."
                    ),
                    "explanation": "The candidate reverses the source.",
                }
            ]
        ),
        "eof_verification": {"complete_to_eof": True},
    }
    _write(report_path, json.dumps(report, indent=2))
    return manifest_path, report_path


def _intake(
    tmp_path: Path,
    manifest_path: Path,
    *,
    policy: PipelinePolicy | None = None,
) -> tuple[PipelineStore, AuditIntakeStore, AuditIntakeItem]:
    store = PipelineStore(
        tmp_path / ".ai-local/pipeline-v1",
        tmp_path,
        policy=policy,
    )
    intake = AuditIntakeStore(store)
    item = intake.create(
        AuditIntakeSpec(
            source_id="codex/intake-test",
            manifest_path=manifest_path.relative_to(tmp_path).as_posix(),
            assigned_reviewer="gpt-5.6-terra",
            provider="glm",
            attempt_id="audit-intake-v1",
        ),
        actor="test",
    )
    return store, intake, item


def _complete_pass_audit(
    tmp_path: Path,
    *,
    policy: PipelinePolicy | None = None,
) -> tuple[PipelineStore, AuditIntakeStore, AuditIntakeItem]:
    manifest_path, report_path = _fixture(tmp_path, verdict="pass")
    store, intake, item = _intake(
        tmp_path,
        manifest_path,
        policy=policy,
    )
    _ = intake.claim_audit(item.intake_id, "terra-worker")
    _ = intake.complete_audit(
        item.intake_id,
        "terra-worker",
        report_path.relative_to(tmp_path).as_posix(),
        duration_ms=AUDIT_DURATION_MS,
    )
    routed = intake.route_completed_audits()
    assert len(routed) == 1
    assert routed[0].state == AuditIntakeState.CLEAN_ADOPTION_READY
    return store, intake, routed[0]


def test_recover_expired_leases_ignores_concurrently_removed_lease(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A worker may remove its lease while recovery scans the directory."""
    manifest_path, _ = _fixture(tmp_path)
    _, intake, item = _intake(tmp_path, manifest_path)
    _ = intake.claim_audit(item.intake_id, "terra-worker")
    lease_path = intake.leases_root / f"{item.intake_id}.json"
    path_type = type(lease_path)
    original_read_text = path_type.read_text

    def disappearing_read_text(
        path: Path,
        *args: object,
        **kwargs: object,
    ) -> str:
        if path == lease_path:
            path.unlink()
            raise FileNotFoundError(path)
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(path_type, "read_text", disappearing_read_text)

    assert intake.recover_expired_leases() == ()


def _clean_adoption_gate(
    repo_root: Path,
    log_path: Path,
) -> SiteGateResult:
    audit_root = (
        repo_root / ".ai-local/audit-materialized/codex/intake-test"
    )
    public_root = repo_root / "docs/ai"
    public_source = public_root / "en/codex/intake-test.md"
    public_candidate = public_root / "zh-CN/codex/intake-test.md"
    _write(
        public_source,
        (audit_root / "en.md").read_text(encoding="utf-8"),
    )
    _write(
        public_candidate,
        (audit_root / "zh-CN.md").read_text(encoding="utf-8"),
    )
    _write(log_path, "all clean adoption gates passed\n")
    return SiteGateResult(
        page_tests=True,
        typecheck=True,
        lint=True,
        materialization=True,
        build=True,
        routes=True,
        duration_ms=123,
        log_path=log_path.relative_to(repo_root).as_posix(),
    )


def _complete_fail_audit(
    tmp_path: Path,
    intake: AuditIntakeStore,
    item: AuditIntakeItem,
    report_path: Path,
) -> AuditIntakeItem:
    _ = intake.claim_audit(item.intake_id, "terra-worker")
    completed = intake.complete_audit(
        item.intake_id,
        "terra-worker",
        report_path.relative_to(tmp_path).as_posix(),
        duration_ms=AUDIT_DURATION_MS,
    )
    assert completed.state == AuditIntakeState.AUDIT_COMPLETE
    routed = intake.route_completed_audits()
    assert len(routed) == 1
    assert routed[0].state == AuditIntakeState.BRIDGE_QUEUED
    return routed[0]


def test_audit_bridge_enters_repair_once_and_releases_reservation(
    tmp_path: Path,
) -> None:
    """Audit and bridge evidence become measurable before targeted repair."""
    manifest_path, report_path = _fixture(tmp_path)
    store, intake, item = _intake(tmp_path, manifest_path)
    assert store.source_reservation(item.source_id) is not None
    routed = _complete_fail_audit(
        tmp_path,
        intake,
        item,
        report_path,
    )

    _ = intake.claim_bridge(routed.intake_id, "bridge-worker")
    queued = intake.complete_bridge(
        routed.intake_id,
        "bridge-worker",
        duration_ms=BRIDGE_DURATION_MS,
    )

    assert queued.state == AuditIntakeState.QUEUED_TO_REPAIR
    assert queued.repair_job_id is not None
    assert store.load_job(queued.repair_job_id).state == (
        PipelineState.REPAIR_QUEUED
    )
    assert store.source_reservation(item.source_id) is None
    status = intake.status()
    assert status.combined_downstream_wip == 1
    metrics = intake.metrics()
    assert metrics.counters["audit_reports"] == 1
    assert metrics.counters["queued_to_repair"] == 1
    assert metrics.stages["audit_service"].total_ms == AUDIT_DURATION_MS
    assert metrics.stages["bridge_service"].total_ms == BRIDGE_DURATION_MS


def test_audit_completion_blocks_non_unique_repair_evidence_before_routing(
    tmp_path: Path,
) -> None:
    """Ambiguous audit excerpts preserve the report without wedging audit WIP."""
    manifest_path, report_path = _fixture(tmp_path)
    payload = cast(
        "dict[str, object]",
        json.loads(report_path.read_text(encoding="utf-8")),
    )
    issues = cast("list[dict[str, object]]", payload["issues"])
    issues[0]["candidate_span_text"] = "Settings"
    _write(report_path, json.dumps(payload, indent=2))
    store, intake, item = _intake(tmp_path, manifest_path)
    _ = intake.claim_audit(item.intake_id, "terra-worker")

    blocked = intake.complete_audit(
        item.intake_id,
        "terra-worker",
        report_path.relative_to(tmp_path).as_posix(),
        duration_ms=AUDIT_DURATION_MS,
    )

    assert blocked.state == AuditIntakeState.STRUCTURAL_BLOCKED
    assert blocked.audit_report_sha256 == sha256_path(report_path)
    assert blocked.audit_verdict == "fail"
    assert blocked.terminal_reason is not None
    assert "bridge preflight failed" in blocked.terminal_reason
    assert "candidate span" in blocked.terminal_reason
    assert store.source_reservation(item.source_id) is None
    assert intake.metrics().stages["audit_service"].total_ms == (
        AUDIT_DURATION_MS
    )
    with pytest.raises(ValueError, match="no running stage"):
        _ = intake.heartbeat(item.intake_id, "terra-worker")


def test_clean_audit_routes_to_adoption_without_creating_repair(
    tmp_path: Path,
) -> None:
    """A clean assigned audit is explicit WIP, not a fabricated no-op repair."""
    manifest_path, report_path = _fixture(tmp_path, verdict="pass")
    store, intake, item = _intake(tmp_path, manifest_path)
    _ = intake.claim_audit(item.intake_id, "terra-worker")
    completed = intake.complete_audit(
        item.intake_id,
        "terra-worker",
        report_path.relative_to(tmp_path).as_posix(),
        duration_ms=900,
    )
    assert completed.state == AuditIntakeState.AUDIT_COMPLETE

    routed = intake.route_completed_audits()

    assert routed[0].state == AuditIntakeState.CLEAN_ADOPTION_READY
    assert store.list_jobs() == ()
    assert store.source_reservation(item.source_id) is not None


def test_clean_adoption_is_gated_recorded_and_releases_source(
    tmp_path: Path,
) -> None:
    """A clean audit adopts raw content only after final public hash gates."""
    store, intake, item = _complete_pass_audit(
        tmp_path,
        policy=PipelinePolicy(promotion_batch_size=1),
    )
    status = intake.status()
    assert status.clean_adoption_ready == 1
    assert status.pre_repair_wip == 1
    assert status.combined_downstream_wip == 1
    snapshot = PipelineDispatcher(store).reconcile()
    assert snapshot.promotion_due is True

    result = CleanAdoptionBatchRunner(
        store,
        gate_runner=_clean_adoption_gate,
        final_shape_checker=lambda _repo_root, _items: None,
        rollback_runner=lambda _repo_root: None,
    ).run_due()

    target = (
        tmp_path
        / "source-ai/content/zh-CN/codex/intake-test.md"
    )
    candidate = (
        tmp_path
        / ".ai-local/staging/dual-review-normalized/codex/intake-test.md"
    )
    assert result.adopted_intake_ids == (item.intake_id,)
    assert target.read_bytes() == candidate.read_bytes()
    adopted = intake.load(item.intake_id)
    assert adopted.state == AuditIntakeState.CLEAN_ADOPTED
    assert adopted.adoption_evidence_path is not None
    assert store.source_reservation(item.source_id) is None
    status = intake.status()
    assert status.clean_adoption_ready == 0
    assert status.combined_downstream_wip == 0
    metrics = intake.metrics()
    assert metrics.counters["clean_adopted"] == 1
    assert metrics.stages["clean_adoption_wait"].samples == 1


def test_clean_adoption_rolls_back_target_when_site_gate_fails(
    tmp_path: Path,
) -> None:
    """A failed gate leaves the audit ready and restores formal content."""
    store, intake, item = _complete_pass_audit(tmp_path)
    rollback_calls: list[Path] = []

    def fail_gate(repo_root: Path, log_path: Path) -> SiteGateResult:
        _ = _clean_adoption_gate(repo_root, log_path)
        msg = "simulated clean adoption gate failure"
        raise ValueError(msg)

    runner = CleanAdoptionBatchRunner(
        store,
        gate_runner=fail_gate,
        final_shape_checker=lambda _repo_root, _items: None,
        rollback_runner=rollback_calls.append,
    )
    with pytest.raises(ValueError, match="simulated"):
        _ = runner.run_due(force=True)

    target = (
        tmp_path
        / "source-ai/content/zh-CN/codex/intake-test.md"
    )
    assert not target.exists()
    assert intake.load(item.intake_id).state == (
        AuditIntakeState.CLEAN_ADOPTION_READY
    )
    assert store.source_reservation(item.source_id) is not None
    assert rollback_calls == [tmp_path]
    transactions = tuple(
        CleanAdoptionTransaction.model_validate_json(
            path.read_text(encoding="utf-8")
        )
        for path in runner.transactions_root.glob("*/intent.json")
    )
    assert len(transactions) == 1
    assert transactions[0].state == "rolled_back"


def test_clean_adoption_recovers_after_gate_passed_commit_interruption(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A crash after gates replays evidence and adoption without rerunning gates."""
    store, intake, item = _complete_pass_audit(tmp_path)
    runner = CleanAdoptionBatchRunner(
        store,
        gate_runner=_clean_adoption_gate,
        final_shape_checker=lambda _repo_root, _items: None,
        rollback_runner=lambda _repo_root: None,
    )
    original_adopt = runner.intake.adopt_clean
    attempts = 0

    def interrupt_adoption(
        intake_id: str,
        evidence_path: str,
        *,
        actor: str,
    ) -> AuditIntakeItem:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            msg = "simulated clean adoption ledger interruption"
            raise RuntimeError(msg)
        return original_adopt(
            intake_id,
            evidence_path,
            actor=actor,
        )

    monkeypatch.setattr(runner.intake, "adopt_clean", interrupt_adoption)
    with pytest.raises(RuntimeError, match="ledger interruption"):
        _ = runner.run_due(force=True)
    transactions = tuple(
        CleanAdoptionTransaction.model_validate_json(
            path.read_text(encoding="utf-8")
        )
        for path in runner.transactions_root.glob("*/intent.json")
    )
    assert transactions[0].state == "gates_passed"
    assert intake.load(item.intake_id).state == (
        AuditIntakeState.CLEAN_ADOPTION_READY
    )

    recovered = runner.run_due(force=True)

    assert recovered.selected_intake_ids == ()
    assert intake.load(item.intake_id).state == (
        AuditIntakeState.CLEAN_ADOPTED
    )
    assert store.source_reservation(item.source_id) is None
    transactions = tuple(
        CleanAdoptionTransaction.model_validate_json(
            path.read_text(encoding="utf-8")
        )
        for path in runner.transactions_root.glob("*/intent.json")
    )
    assert transactions[0].state == "recorded"


def test_active_intake_blocks_unrelated_repair_for_same_source(
    tmp_path: Path,
) -> None:
    """Shared source ownership prevents audit and repair duplication."""
    manifest_path, report_path = _fixture(tmp_path)
    store, _intake_store, item = _intake(tmp_path, manifest_path)
    review = bridge_deep_audit_report(
        repo_root=tmp_path,
        manifest_path=manifest_path,
        report_path=report_path,
        source_id=item.source_id,
        assigned_reviewer=item.assigned_reviewer,
    )
    repair_review_path = tmp_path / ".ai-local/repair-ready/manual.json"
    write_repair_ready_review(repair_review_path, review)
    spec = RepairJobSpec(
        source_id=review.source_id,
        source_path=review.source_path,
        candidate_path=review.candidate_path,
        source_sha256=review.source_sha256,
        base_candidate_sha256=review.candidate_sha256,
        review_path=repair_review_path.relative_to(tmp_path).as_posix(),
        assigned_reviewer=review.assigned_reviewer,
        provider="glm",
        provider_model="glm-5.2",
        attempt_id="unrelated-repair",
    )

    with pytest.raises(ValueError, match="reserved by an active intake"):
        _ = store.create_job(spec, actor="test")


def test_bridge_replays_after_repair_job_precedes_intake_event(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A crash between the two ledgers resumes without duplicate source work."""
    manifest_path, report_path = _fixture(tmp_path)
    store, intake, item = _intake(tmp_path, manifest_path)
    routed = _complete_fail_audit(
        tmp_path,
        intake,
        item,
        report_path,
    )
    _ = intake.claim_bridge(routed.intake_id, "bridge-worker")
    original_transition = intake._transition  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
    interrupted = False

    def interrupt_bridge_commit(  # noqa: PLR0913
        current: AuditIntakeItem,
        *,
        state: AuditIntakeState,
        kind: AuditIntakeEventKind,
        actor: str,
        idempotency_key: str,
        duration_ms: int | None = None,
        reason: str | None = None,
    ) -> AuditIntakeItem:
        nonlocal interrupted
        if state == AuditIntakeState.BRIDGE_VERIFIED and not interrupted:
            interrupted = True
            message = "synthetic cross-ledger interruption"
            raise RuntimeError(message)
        return original_transition(
            current,
            state=state,
            kind=kind,
            actor=actor,
            idempotency_key=idempotency_key,
            duration_ms=duration_ms,
            reason=reason,
        )

    monkeypatch.setattr(intake, "_transition", interrupt_bridge_commit)
    with pytest.raises(RuntimeError, match="cross-ledger interruption"):
        _ = intake.complete_bridge(
            routed.intake_id,
            "bridge-worker",
            duration_ms=BRIDGE_DURATION_MS,
        )

    assert len(store.list_jobs()) == 1
    assert intake.load(item.intake_id).state == (
        AuditIntakeState.BRIDGE_RUNNING
    )

    monkeypatch.setattr(intake, "_transition", original_transition)
    recovered = intake.complete_bridge(
        routed.intake_id,
        "bridge-worker",
        duration_ms=BRIDGE_DURATION_MS,
    )

    assert recovered.state == AuditIntakeState.QUEUED_TO_REPAIR
    assert len(store.list_jobs()) == 1
    assert store.source_reservation(item.source_id) is None


def test_dispatcher_continuously_ingests_audit_and_auto_bridges(
    tmp_path: Path,
) -> None:
    """One dispatcher cycle removes report-ingestion and bridge wave gaps."""
    manifest_path, report_path = _fixture(tmp_path)
    store, intake, item = _intake(tmp_path, manifest_path)
    dispatcher = PipelineDispatcher(store)
    initial = dispatcher.reconcile()
    assert [
        action.stage for action in initial.actions
    ] == [DispatchStage.AUDIT]
    claim = dispatcher.claim_next(
        DispatchStage.AUDIT,
        "gpt-5.6-terra",
        "terra-worker",
    )
    assert claim.claimed is True
    _ = dispatcher.submit_completion(
        CompletionEnvelope(
            completion_id="audit-intake-test",
            kind=CompletionKind.DEEP_AUDIT,
            job_id=item.intake_id,
            worker_id="terra-worker",
            report_path=report_path.relative_to(tmp_path).as_posix(),
            duration_ms=AUDIT_DURATION_MS,
        )
    )

    completed = dispatcher.run(max_cycles=1, auto_bridge=True)

    assert (
        dispatcher.processed_root / "audit-intake-test.json"
    ).is_file()
    assert completed.bridge_due is False
    assert intake.load(item.intake_id).state == (
        AuditIntakeState.QUEUED_TO_REPAIR
    )
    assert len(store.list_jobs()) == 1
    assert any(
        action.stage == DispatchStage.REPAIR
        for action in completed.actions
    )
