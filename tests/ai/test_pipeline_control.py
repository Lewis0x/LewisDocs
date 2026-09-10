# Copyright 2026
# ruff: noqa: INP001, S101

"""Tests for quality-gated continuous deep-audit admission."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING

from scripts.ai.audit_admission import AdmittedAudit, AuditAdmissionBatch
from scripts.ai.pipeline import PipelineStore
from scripts.ai.pipeline_control import (
    AdmissionControlDecision,
    AdmissionControlPolicy,
    AdmissionPhase,
    AdmissionQualitySnapshot,
    ContinuousAuditAdmissionController,
    admission_quality_failure,
)

if TYPE_CHECKING:
    import pytest

_TRANSIENT_LOCK_FAILURES = 2
EXPECTED_DEFAULT_WORKFLOW_VERSION = 3
EXPECTED_DEFAULT_BATCH_PAGES = 4


def _quality(
    *,
    clean: int,
    nonpass: int,
    invalid: int = 0,
    audit_terminal: int = 5,
) -> AdmissionQualitySnapshot:
    samples = clean + nonpass
    return AdmissionQualitySnapshot(
        admitted_pages=12,
        active_pages=max(12 - samples, 0),
        audit_terminal_pages=audit_terminal,
        invalid_audits=invalid,
        final_samples=samples,
        clean_final_pages=clean,
        post_repair_issue_pages=nonpass,
        clean_yield=clean / samples if samples else None,
        post_repair_issue_rate=nonpass / samples if samples else None,
        invalid_audit_rate=invalid / audit_terminal if audit_terminal else None,
    )


def test_quality_gate_waits_for_bounded_pilot_sample() -> None:
    """A single surprising final review cannot trigger speculative scaling."""
    assert (
        admission_quality_failure(
            AdmissionControlPolicy(),
            _quality(clean=0, nonpass=1),
        )
        is None
    )


def test_quality_gate_pauses_when_final_review_finds_more_issues() -> None:
    """Post-repair issue discovery above twenty percent halts admission."""
    reason = admission_quality_failure(
        AdmissionControlPolicy(),
        _quality(clean=3, nonpass=2),
    )

    assert reason == "post-repair full-page issue rate exceeds the quality limit"


def test_quality_gate_allows_high_yield_sample() -> None:
    """Four clean pages and one nonpass satisfy the conservative pilot gate."""
    assert (
        admission_quality_failure(
            AdmissionControlPolicy(),
            _quality(clean=4, nonpass=1),
        )
        is None
    )


def test_quality_gate_pauses_on_invalid_audits_before_final_reviews() -> None:
    """Contract failures stop scale-out after a minimally useful audit sample."""
    reason = admission_quality_failure(
        AdmissionControlPolicy(),
        _quality(
            clean=0,
            nonpass=0,
            invalid=1,
            audit_terminal=5,
        ),
    )

    assert reason == "deep-audit contract invalid rate exceeds the quality limit"


def test_admission_phase_values_are_stable() -> None:
    """Persisted controller statuses remain machine-readable."""
    assert AdmissionPhase.WAITING_FOR_QUALITY.value == "waiting_for_quality"
    assert AdmissionPhase.PAUSED_ON_QUALITY.value == "paused_on_quality"


def test_default_admission_policy_uses_v3_deep_audit() -> None:
    """New automatic admissions use the recall-hardened workflow."""
    policy = AdmissionControlPolicy()

    assert policy.review_workflow_version == EXPECTED_DEFAULT_WORKFLOW_VERSION
    assert policy.batch_prefix == "deep-audit-v3-flow"
    assert policy.max_batch_pages == EXPECTED_DEFAULT_BATCH_PAGES
    assert not policy.allow_quality_reset


def test_fresh_prefix_cannot_bypass_persisted_quality_pause(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Renaming a cohort cannot silently reset a failed quality gate."""
    store = PipelineStore(tmp_path / "pipeline", tmp_path)
    controller = ContinuousAuditAdmissionController(
        store,
        policy=AdmissionControlPolicy(batch_prefix="fresh-flow"),
    )
    previous = AdmissionControlDecision(
        generated_at=datetime.now(UTC),
        phase=AdmissionPhase.PAUSED_ON_QUALITY,
        reason="post-repair issue rate is too high",
        combined_wip=0,
        free_slots=12,
        eligible_pages=0,
        admitted_count=0,
        quality=_quality(clean=2, nonpass=2, audit_terminal=4),
    )
    controller.status_path.parent.mkdir(parents=True)
    _ = controller.status_path.write_text(
        previous.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
    )

    def unexpected_inventory(*_args: object, **_kwargs: object) -> object:
        message = "a persisted quality pause must stop before inventory admission"
        raise AssertionError(message)

    monkeypatch.setattr(
        "scripts.ai.pipeline_control.build_inventory",
        unexpected_inventory,
    )

    decision = controller.tick()

    assert decision.phase == AdmissionPhase.PAUSED_ON_QUALITY
    assert decision.admitted_count == 0
    assert decision.quality == previous.quality
    assert not tuple((store.root / "admission-batches").glob("*.json"))


def test_status_write_retries_a_transient_windows_file_lock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A short-lived reader lock must not terminate the dispatcher."""
    controller = ContinuousAuditAdmissionController(
        PipelineStore(tmp_path / "pipeline", tmp_path)
    )
    original_replace = Path.replace
    attempts = 0

    def flaky_replace(path: Path, target: Path) -> Path:
        nonlocal attempts
        if (
            target == controller.status_path
            and attempts < _TRANSIENT_LOCK_FAILURES
        ):
            attempts += 1
            message = "simulated Windows reader lock"
            raise PermissionError(message)
        attempts += 1
        return original_replace(path, target)

    def no_sleep(_delay: float) -> None:
        pass

    def empty_inventory(
        *_args: object,
        **_kwargs: object,
    ) -> SimpleNamespace:
        return SimpleNamespace(items=())

    monkeypatch.setattr(Path, "replace", flaky_replace)
    monkeypatch.setattr(
        "scripts.ai.pipeline_control.time.sleep",
        no_sleep,
    )
    monkeypatch.setattr(
        "scripts.ai.pipeline_control.build_inventory",
        empty_inventory,
    )

    decision = controller.tick()

    persisted = type(decision).model_validate_json(
        controller.status_path.read_text(encoding="utf-8")
    )
    assert persisted == decision
    assert attempts == _TRANSIENT_LOCK_FAILURES + 1
    assert not tuple(controller.status_path.parent.glob("*.tmp"))


def test_quality_batches_are_isolated_by_policy_prefix(
    tmp_path: Path,
) -> None:
    """A remediated cohort must not inherit an older cohort's quality sample."""
    store = PipelineStore(tmp_path / "pipeline", tmp_path)
    batch_root = store.root / "admission-batches"
    batch_root.mkdir(parents=True)

    def write_batch(prefix: str, suffix: str) -> None:
        batch = AuditAdmissionBatch(
            batch_id=f"{prefix}-0001",
            plan_path=f"{prefix}.plan.json",
            plan_sha256="0" * 64,
            manifest_path=f"{prefix}.manifest.json",
            manifest_sha256="1" * 64,
            admitted=(
                AdmittedAudit(
                    source_id=f"codex/{suffix}",
                    intake_id=("2" if suffix == "old" else "3") * 64,
                    assigned_reviewer="gpt-5.6-terra",
                    repair_provider="glm",
                    attempt_id=f"{prefix}-{suffix}",
                ),
            ),
        )
        _ = (batch_root / f"{batch.batch_id}.json").write_text(
            batch.model_dump_json(indent=2) + "\n",
            encoding="utf-8",
        )

    write_batch("deep-audit-v2-flow", "old")
    write_batch("deep-audit-v3-flow", "new")
    controller = ContinuousAuditAdmissionController(
        store,
        policy=AdmissionControlPolicy(batch_prefix="deep-audit-v3-flow"),
    )

    batches = controller._load_batches()  # pyright: ignore[reportPrivateUsage] # noqa: SLF001

    assert [batch.batch_id for batch in batches] == [
        "deep-audit-v3-flow-0001"
    ]
