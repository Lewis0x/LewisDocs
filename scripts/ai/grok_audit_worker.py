# Copyright 2026

"""Run one hash-bound Grok deep audit through the local CLI."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Annotated,
    ClassVar,
    Final,
    Literal,
    cast,
)

import typer
from pydantic import BaseModel, ConfigDict, Field, RootModel, ValidationError

from scripts.ai.audit_coverage import (
    DeepAuditFindingReport,
)
from scripts.ai.audit_v3 import (
    AuditV3Plan,
    AuditV3SliceReport,
    validate_audit_v3_slice_report,
)
from scripts.ai.audit_worker import (
    AuditWorkerManifest,
    AuditWorkerSliceArtifact,
    canonicalize_audit_v3_slice_report,
    finalize_assigned_audit_worker,
)
from scripts.ai.pipeline import PipelineStore
from scripts.ai.pipeline_intake import AuditIntakeState, AuditIntakeStore
from scripts.ai.review_contract import resolve_repo_path, sha256_path

if TYPE_CHECKING:
    from collections.abc import Callable

    from scripts.ai.pipeline_dispatcher import CompletionEnvelope

_DEFAULT_REPO_ROOT: Final = Path()
_DEFAULT_PIPELINE_ROOT: Final = Path(".ai-local/pipeline-v1")
_MAX_INVALID_SLICE_RETRIES: Final = 1
_REVIEW_WORKFLOW_V3: Final = 3


class _StrictModel(BaseModel):
    """Base for local Grok worker records."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )


class _JsonObject(RootModel[dict[str, object]]):
    """Typed JSON object used to contain decoder output."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True,
        strict=True,
    )


class GrokAuditWorkerStatus(_StrictModel):
    """Redacted progress record for one Grok deep-audit process."""

    version: Literal[1] = 1
    state: Literal["running", "completed", "error"]
    intake_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_id: str
    worker_id: str
    started_at: datetime
    updated_at: datetime
    duration_ms: int | None = Field(default=None, ge=0)
    report_path: str | None = None
    report_sha256: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )
    active_slice_id: str | None = None
    completed_slices: int = Field(default=0, ge=0)
    total_slices: int = Field(default=1, ge=1)
    invalid_attempt_count: int = Field(default=0, ge=0)
    error_type: str | None = None


class InvalidSliceFindingsError(ValueError):
    """A model-authored slice failed schema or exact-excerpt validation."""


class InvalidFinalReportError(ValueError):
    """Valid slices could not form one unambiguous final report."""


def _is_final_report_contract_error(error: Exception) -> bool:
    """Recognize deterministic model-authored merge conflicts only."""
    return isinstance(error, ValueError) and (
        "refers to conflicting exact spans" in str(error)
    )


def _finalize_validated_grok_worker(
    intake_store: AuditIntakeStore,
    *,
    worker_manifest_path: Path,
    duration_ms: int,
) -> CompletionEnvelope:
    """Convert deterministic model id collisions into terminal audit errors."""
    try:
        return finalize_assigned_audit_worker(
            intake_store,
            worker_manifest_path=worker_manifest_path,
            duration_ms=duration_ms,
        )
    except ValueError as error:
        if not _is_final_report_contract_error(error):
            raise
        raise InvalidFinalReportError(str(error)) from error


def _terminal_contract_reason(error: Exception) -> str | None:
    """Return the immutable intake reason for a rejected Grok report."""
    if isinstance(error, InvalidSliceFindingsError):
        return (
            "Grok slice exact-evidence validation exhausted its bounded "
            f"retry: {_redacted_validation_error(error)}"
        )[:500]
    if isinstance(error, InvalidFinalReportError):
        return (
            "Grok final report has conflicting model-authored issue "
            f"identity: {_redacted_validation_error(error)}"
        )[:500]
    return None


def parse_grok_cli_output(stdout: str) -> tuple[dict[str, object], int]:
    """Extract the final schema payload from one Grok JSON envelope."""
    envelope = _JsonObject.model_validate(
        cast("object", json.loads(stdout))
    ).root
    stop_reason = str(envelope.get("stopReason", "")).lower()
    if stop_reason in {"cancelled", "error", "failed"}:
        message = f"Grok CLI stopped with {stop_reason}"
        raise ValueError(message)
    structured_output = envelope.get("structuredOutput")
    if isinstance(structured_output, dict):
        return _JsonObject.model_validate(structured_output).root, 0
    value = envelope.get("text")
    if isinstance(value, dict):
        return _JsonObject.model_validate(value).root, 0
    if not isinstance(value, str):
        message = "Grok CLI returned no structured report"
        raise TypeError(message)
    payloads = _parse_concatenated_objects(value)
    return payloads[-1], len(payloads) - 1


def run_grok_audit_worker(  # noqa: PLR0913, PLR0915
    *,
    worker_manifest_path: Path,
    repo_root: Path,
    pipeline_root: Path,
    heartbeat_seconds: float = 45.0,
    timeout_seconds: float = 45.0 * 60.0,
    grok_command: str | None = None,
) -> CompletionEnvelope:
    """Run, locally validate, and submit one assigned Grok deep audit."""
    repo_root = repo_root.resolve()
    pipeline_root = pipeline_root.resolve()
    manifest = AuditWorkerManifest.model_validate_json(
        worker_manifest_path.read_text(encoding="utf-8-sig")
    )
    if manifest.assigned_reviewer != "grok-4.5":
        message = "Grok worker received a non-Grok assigned review"
        raise ValueError(message)
    if heartbeat_seconds <= 0 or timeout_seconds <= 0:
        message = "worker heartbeat and timeout must be positive"
        raise ValueError(message)

    paths = _validate_worker_artifacts(repo_root, manifest)
    plan = (
        AuditV3Plan.model_validate_json(
            paths["v3_plan"].read_text(encoding="utf-8-sig")
        )
        if manifest.review_workflow_version == _REVIEW_WORKFLOW_V3
        else None
    )
    plan_sha256 = plan.plan_sha256 if plan is not None else None
    coverage_contract_sha256 = (
        plan.coverage_contract_sha256 if plan is not None else None
    )
    store = PipelineStore(pipeline_root, repo_root)
    intake_store = AuditIntakeStore(store)
    item = intake_store.load(manifest.intake_id)
    if (
        item.state != AuditIntakeState.AUDIT_RUNNING
        or item.source_id != manifest.source_id
        or item.assigned_reviewer != manifest.assigned_reviewer
    ):
        message = "Grok worker manifest does not own the active audit lease"
        raise ValueError(message)
    _ = intake_store.heartbeat(manifest.intake_id, manifest.worker_id)

    started_at = datetime.now(UTC)
    started = time.perf_counter()
    status_path = paths["status"]
    stdout_path = status_path.with_name("grok-cli.stdout.json")
    stderr_path = status_path.with_name("grok-cli.stderr.log")
    completed_slices = 0
    total_slices = len(manifest.slices) if manifest.slices else 1
    invalid_attempt_count = _count_invalid_attempts(repo_root, manifest)
    _write_status(
        status_path,
        GrokAuditWorkerStatus(
            state="running",
            intake_id=manifest.intake_id,
            source_id=manifest.source_id,
            worker_id=manifest.worker_id,
            started_at=started_at,
            updated_at=started_at,
            invalid_attempt_count=invalid_attempt_count,
        ),
    )

    try:
        environment = os.environ.copy()
        _ = environment.setdefault("HOME", str(Path.home()))
        _ = environment.setdefault("GROK_HOME", str(Path.home() / ".grok"))
        slices = manifest.slices

        def heartbeat(active_slice_id: str | None) -> None:
            _ = intake_store.heartbeat(
                manifest.intake_id,
                manifest.worker_id,
            )
            _write_status(
                status_path,
                GrokAuditWorkerStatus(
                    state="running",
                    intake_id=manifest.intake_id,
                    source_id=manifest.source_id,
                    worker_id=manifest.worker_id,
                    started_at=started_at,
                    updated_at=datetime.now(UTC),
                    active_slice_id=active_slice_id,
                    completed_slices=completed_slices,
                    total_slices=total_slices,
                    invalid_attempt_count=invalid_attempt_count,
                ),
            )

        if slices:
            for artifact in slices:
                findings_path = resolve_repo_path(
                    repo_root,
                    artifact.findings_path,
                )
                slice_status = resolve_repo_path(
                    repo_root,
                    artifact.status_path,
                )
                slice_stdout = slice_status.with_name(
                    f"{slice_status.stem}.grok-cli.stdout.json"
                )
                slice_stderr = slice_status.with_name(
                    f"{slice_status.stem}.grok-cli.stderr.log"
                )
                heartbeat(artifact.slice_id)
                command = grok_command or _find_grok()
                slice_schema_path = resolve_repo_path(
                    repo_root,
                    artifact.schema_path,
                )
                active_slice_id = artifact.slice_id

                def invoke_slice(
                    prompt_path: Path,
                    stdout_target: Path,
                    stderr_target: Path,
                    *,
                    _command: str = command,
                    _schema_path: Path = slice_schema_path,
                    _slice_id: str = active_slice_id,
                ) -> dict[str, object]:
                    return _invoke_grok_cli(
                        grok_command=_command,
                        repo_root=repo_root,
                        prompt_path=prompt_path,
                        schema_path=_schema_path,
                        stdout_path=stdout_target,
                        stderr_path=stderr_target,
                        environment=environment,
                        heartbeat_seconds=heartbeat_seconds,
                        timeout_seconds=timeout_seconds,
                        on_heartbeat=lambda: heartbeat(_slice_id),
                    )

                findings, new_invalid_attempts = _load_or_run_valid_slice(
                    manifest=manifest,
                    artifact=artifact,
                    plan=plan,
                    plan_sha256=cast("str", plan_sha256),
                    coverage_contract_sha256=cast(
                        "str",
                        coverage_contract_sha256,
                    ),
                    findings_path=findings_path,
                    source_path=paths["source"],
                    candidate_path=paths["candidate"],
                    repair_source_path=paths["repair_source"],
                    repair_candidate_path=paths["repair_candidate"],
                    original_prompt_path=resolve_repo_path(
                        repo_root,
                        artifact.prompt_path,
                    ),
                    original_stdout_path=slice_stdout,
                    original_stderr_path=slice_stderr,
                    invoke=invoke_slice,
                )
                invalid_attempt_count += new_invalid_attempts
                _atomic_json(
                    findings_path,
                    findings.model_dump(mode="json", by_alias=True),
                )
                completed_slices += 1
                _write_status(
                    slice_status,
                    GrokAuditWorkerStatus(
                        state="completed",
                        intake_id=manifest.intake_id,
                        source_id=manifest.source_id,
                        worker_id=manifest.worker_id,
                        started_at=started_at,
                        updated_at=datetime.now(UTC),
                        active_slice_id=artifact.slice_id,
                        completed_slices=completed_slices,
                        total_slices=total_slices,
                        invalid_attempt_count=invalid_attempt_count,
                    ),
                )
        else:
            payload = _invoke_grok_cli(
                grok_command=grok_command or _find_grok(),
                repo_root=repo_root,
                prompt_path=paths["prompt"],
                schema_path=paths["schema"],
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                environment=environment,
                heartbeat_seconds=heartbeat_seconds,
                timeout_seconds=timeout_seconds,
                on_heartbeat=lambda: heartbeat(None),
            )
            findings = DeepAuditFindingReport.model_validate(payload)
            _atomic_json(
                paths["findings"],
                findings.model_dump(mode="json", by_alias=True),
            )
            completed_slices = 1
        duration_ms = max(0, round((time.perf_counter() - started) * 1000))
        completion = _finalize_validated_grok_worker(
            intake_store,
            worker_manifest_path=worker_manifest_path,
            duration_ms=duration_ms,
        )
        report_path = paths["report"]
        report_sha256 = sha256_path(report_path)
        completion_path = status_path.with_name("completion.json")
        _atomic_json(
            completion_path,
            completion.model_dump(mode="json"),
        )
        _write_status(
            status_path,
            GrokAuditWorkerStatus(
                state="completed",
                intake_id=manifest.intake_id,
                source_id=manifest.source_id,
                worker_id=manifest.worker_id,
                started_at=started_at,
                updated_at=datetime.now(UTC),
                duration_ms=duration_ms,
                report_path=_relative(repo_root, report_path),
                report_sha256=report_sha256,
                completed_slices=completed_slices,
                total_slices=total_slices,
                invalid_attempt_count=invalid_attempt_count,
            ),
        )
        return completion  # noqa: TRY300
    except Exception as error:
        invalid_attempt_count = _count_invalid_attempts(repo_root, manifest)
        reason = _terminal_contract_reason(error)
        if reason is not None:
            _ = intake_store.block(
                manifest.intake_id,
                actor=manifest.worker_id,
                reason=reason,
            )
        _write_status(
            status_path,
            GrokAuditWorkerStatus(
                state="error",
                intake_id=manifest.intake_id,
                source_id=manifest.source_id,
                worker_id=manifest.worker_id,
                started_at=started_at,
                updated_at=datetime.now(UTC),
                duration_ms=max(
                    0,
                    round((time.perf_counter() - started) * 1000),
                ),
                completed_slices=completed_slices,
                total_slices=total_slices,
                invalid_attempt_count=invalid_attempt_count,
                error_type=type(error).__name__,
            ),
        )
        raise


def _validate_worker_artifacts(
    repo_root: Path,
    manifest: AuditWorkerManifest,
) -> dict[str, Path]:
    values = {
        "source": (
            resolve_repo_path(repo_root, manifest.source_path),
            manifest.source_sha256,
        ),
        "candidate": (
            resolve_repo_path(repo_root, manifest.candidate_path),
            manifest.candidate_sha256,
        ),
        "prompt": (
            resolve_repo_path(repo_root, manifest.prompt_path),
            manifest.prompt_sha256,
        ),
        "schema": (
            resolve_repo_path(repo_root, manifest.schema_path),
            manifest.schema_sha256,
        ),
    }
    if manifest.review_workflow_version == _REVIEW_WORKFLOW_V3:
        values.update(
            {
                "repair_source": (
                    resolve_repo_path(
                        repo_root,
                        cast("str", manifest.repair_source_path),
                    ),
                    cast("str", manifest.repair_source_sha256),
                ),
                "repair_candidate": (
                    resolve_repo_path(
                        repo_root,
                        cast("str", manifest.repair_candidate_path),
                    ),
                    cast("str", manifest.repair_candidate_sha256),
                ),
                "v3_context": (
                    resolve_repo_path(
                        repo_root,
                        cast("str", manifest.v3_context_path),
                    ),
                    cast("str", manifest.v3_context_sha256),
                ),
                "v3_plan": (
                    resolve_repo_path(
                        repo_root,
                        cast("str", manifest.v3_plan_path),
                    ),
                    cast("str", manifest.v3_plan_sha256),
                ),
            }
        )
    for label, (path, expected_sha256) in values.items():
        if sha256_path(path) != expected_sha256:
            message = f"Grok worker {label} hash changed"
            raise ValueError(message)
    for artifact in manifest.slices:
        slice_values = (
            (
                resolve_repo_path(repo_root, artifact.prompt_path),
                artifact.prompt_sha256,
                "prompt",
            ),
            (
                resolve_repo_path(repo_root, artifact.schema_path),
                artifact.schema_sha256,
                "schema",
            ),
        )
        for path, expected_sha256, label in slice_values:
            if sha256_path(path) != expected_sha256:
                message = (
                    f"Grok worker {artifact.slice_id} {label} hash changed"
                )
                raise ValueError(message)
    return {
        **{label: value[0] for label, value in values.items()},
        "report": resolve_repo_path(repo_root, manifest.report_path),
        "findings": resolve_repo_path(repo_root, manifest.findings_path),
        "status": resolve_repo_path(repo_root, manifest.status_path),
    }


def _invoke_grok_cli(  # noqa: PLR0913
    *,
    grok_command: str,
    repo_root: Path,
    prompt_path: Path,
    schema_path: Path,
    stdout_path: Path,
    stderr_path: Path,
    environment: dict[str, str],
    heartbeat_seconds: float,
    timeout_seconds: float,
    on_heartbeat: Callable[[], None],
) -> dict[str, object]:
    command = [
        grok_command,
        "--cwd",
        str(repo_root),
        "--model",
        "grok-4.5",
        "--reasoning-effort",
        "high",
        "--disable-web-search",
        "--no-memory",
        "--no-subagents",
        "--no-plan",
        "--permission-mode",
        "dontAsk",
        "--max-turns",
        "40",
        "--tools",
        "Read,Glob,Grep",
        "--json-schema",
        schema_path.read_text(encoding="utf-8-sig"),
        "--prompt-file",
        str(prompt_path),
    ]
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_path.parent.mkdir(parents=True, exist_ok=True)
    with (
        stdout_path.open("w", encoding="utf-8", newline="\n") as stdout_stream,
        stderr_path.open("w", encoding="utf-8", newline="\n") as stderr_stream,
    ):
        process = subprocess.Popen(  # noqa: S603
            command,
            cwd=repo_root,
            env=environment,
            stdout=stdout_stream,
            stderr=stderr_stream,
            text=True,
            encoding="utf-8",
            errors="strict",
        )
        deadline = time.monotonic() + timeout_seconds
        next_heartbeat = time.monotonic() + heartbeat_seconds
        while process.poll() is None:
            now = time.monotonic()
            if now >= deadline:
                process.kill()
                _ = process.wait(timeout=30)
                message = "Grok audit exceeded its bounded timeout"
                raise TimeoutError(message)
            if now >= next_heartbeat:
                on_heartbeat()
                next_heartbeat = now + heartbeat_seconds
            time.sleep(min(2.0, max(0.1, deadline - now)))
        return_code = process.wait()
    if return_code != 0:
        message = f"Grok CLI exited with code {return_code}"
        raise RuntimeError(message)
    payload, _ignored_preliminary = parse_grok_cli_output(
        stdout_path.read_text(encoding="utf-8-sig")
    )
    return payload


def _load_or_run_valid_slice(  # noqa: PLR0913
    *,
    manifest: AuditWorkerManifest,
    artifact: AuditWorkerSliceArtifact,
    plan: AuditV3Plan | None = None,
    plan_sha256: str,
    coverage_contract_sha256: str,
    findings_path: Path,
    source_path: Path,
    candidate_path: Path,
    repair_source_path: Path | None = None,
    repair_candidate_path: Path | None = None,
    original_prompt_path: Path,
    original_stdout_path: Path,
    original_stderr_path: Path,
    invoke: Callable[[Path, Path, Path], dict[str, object]],
) -> tuple[AuditV3SliceReport, int]:
    """Reuse one valid cache or run one original plus one correction attempt."""
    new_invalid_attempts = 0
    try:
        cached = _valid_cached_slice(
            manifest,
            artifact,
            findings_path,
            plan=plan,
            plan_sha256=plan_sha256,
            coverage_contract_sha256=coverage_contract_sha256,
            source_path=source_path,
            candidate_path=candidate_path,
            repair_source_path=repair_source_path,
            repair_candidate_path=repair_candidate_path,
        )
    except InvalidSliceFindingsError as error:
        invalid_payload = _read_invalid_payload(findings_path)
        new_invalid_attempts += int(
            _archive_invalid_payload(
                findings_path,
                attempt=1,
                payload=invalid_payload,
                error=error,
            )
        )
        if _invalid_attempt_path(findings_path, 2).is_file():
            message = (
                f"Grok slice {artifact.slice_id} exhausted its bounded "
                "correction attempt"
            )
            raise InvalidSliceFindingsError(message) from error
        validation_error = error
    else:
        if cached is not None:
            return cached, new_invalid_attempts
        payload = invoke(
            original_prompt_path,
            original_stdout_path,
            original_stderr_path,
        )
        try:
            report = _validate_slice_payload(
                payload,
                manifest=manifest,
                artifact=artifact,
                plan=plan,
                plan_sha256=plan_sha256,
                coverage_contract_sha256=coverage_contract_sha256,
                source_path=source_path,
                candidate_path=candidate_path,
                repair_source_path=repair_source_path,
                repair_candidate_path=repair_candidate_path,
            )
        except InvalidSliceFindingsError as error:
            new_invalid_attempts += int(
                _archive_invalid_payload(
                    findings_path,
                    attempt=1,
                    payload=payload,
                    error=error,
                )
            )
            _atomic_json(findings_path, payload)
            invalid_payload = payload
            validation_error = error
        else:
            return report, new_invalid_attempts

    retry_number = _MAX_INVALID_SLICE_RETRIES
    retry_prompt_path = findings_path.with_name(
        f"{findings_path.stem}.retry-{retry_number:02d}.txt"
    )
    retry_prompt = _build_slice_retry_prompt(
        original_prompt=original_prompt_path.read_text(encoding="utf-8-sig"),
        invalid_payload=invalid_payload,
        validation_error=validation_error,
    )
    _atomic_text(retry_prompt_path, retry_prompt)
    retry_stdout_path = original_stdout_path.with_name(
        f"{original_stdout_path.stem}.retry-{retry_number:02d}.json"
    )
    retry_stderr_path = original_stderr_path.with_name(
        f"{original_stderr_path.stem}.retry-{retry_number:02d}.log"
    )
    retry_payload = invoke(
        retry_prompt_path,
        retry_stdout_path,
        retry_stderr_path,
    )
    try:
        corrected = _validate_slice_payload(
            retry_payload,
            manifest=manifest,
            artifact=artifact,
            plan=plan,
            plan_sha256=plan_sha256,
            coverage_contract_sha256=coverage_contract_sha256,
            source_path=source_path,
            candidate_path=candidate_path,
            repair_source_path=repair_source_path,
            repair_candidate_path=repair_candidate_path,
        )
    except InvalidSliceFindingsError as error:
        new_invalid_attempts += int(
            _archive_invalid_payload(
                findings_path,
                attempt=2,
                payload=retry_payload,
                error=error,
            )
        )
        _atomic_json(findings_path, retry_payload)
        message = (
            f"Grok slice {artifact.slice_id} exhausted its bounded "
            "correction attempt"
        )
        raise InvalidSliceFindingsError(message) from error
    return corrected, new_invalid_attempts


def _valid_cached_slice(  # noqa: PLR0913
    manifest: AuditWorkerManifest,
    artifact: AuditWorkerSliceArtifact,
    findings_path: Path,
    *,
    plan: AuditV3Plan | None = None,
    plan_sha256: str,
    coverage_contract_sha256: str,
    source_path: Path,
    candidate_path: Path,
    repair_source_path: Path | None = None,
    repair_candidate_path: Path | None = None,
) -> AuditV3SliceReport | None:
    if not findings_path.is_file():
        return None
    payload = _read_invalid_payload(findings_path)
    return _validate_slice_payload(
        payload,
        manifest=manifest,
        artifact=artifact,
        plan=plan,
        plan_sha256=plan_sha256,
        coverage_contract_sha256=coverage_contract_sha256,
        source_path=source_path,
        candidate_path=candidate_path,
        repair_source_path=repair_source_path,
        repair_candidate_path=repair_candidate_path,
    )


def _validate_slice_payload(  # noqa: PLR0913
    payload: object,
    *,
    manifest: AuditWorkerManifest,
    artifact: AuditWorkerSliceArtifact,
    plan: AuditV3Plan | None = None,
    plan_sha256: str,
    coverage_contract_sha256: str,
    source_path: Path,
    candidate_path: Path,
    repair_source_path: Path | None = None,
    repair_candidate_path: Path | None = None,
) -> AuditV3SliceReport:
    payload = _bind_deterministic_slice_fields(
        payload,
        manifest=manifest,
        artifact=artifact,
        plan=plan,
        plan_sha256=plan_sha256,
        coverage_contract_sha256=coverage_contract_sha256,
    )
    try:
        report = AuditV3SliceReport.model_validate(payload)
    except (TypeError, ValidationError, ValueError) as error:
        message = (
            f"Grok slice {artifact.slice_id} returned invalid report schema: "
            f"{_redacted_validation_error(error)}"
        )
        raise InvalidSliceFindingsError(message) from error
    identity = (
        (report.slice_id, artifact.slice_id),
        (report.slice_sha256, artifact.slice_sha256),
        (report.source_id, manifest.source_id),
        (report.assigned_reviewer, manifest.assigned_reviewer),
        (report.review_model, manifest.assigned_reviewer),
        (report.source_sha256, manifest.source_sha256),
        (report.candidate_sha256, manifest.candidate_sha256),
        (report.plan_sha256, plan_sha256),
        (
            report.coverage_contract_sha256,
            coverage_contract_sha256,
        ),
    )
    if any(actual != expected for actual, expected in identity):
        message = f"cached Grok slice identity changed: {artifact.slice_id}"
        raise InvalidSliceFindingsError(message)
    canonical = _canonicalize_slice_report(
        report,
        source_path=source_path,
        candidate_path=candidate_path,
        repair_source_path=repair_source_path,
        repair_candidate_path=repair_candidate_path,
    )
    if plan is not None:
        planned = tuple(
            audit_slice
            for audit_slice in plan.slices
            if audit_slice.slice_id == artifact.slice_id
        )
        if len(planned) != 1:
            message = f"Grok slice {artifact.slice_id} is absent from its plan"
            raise InvalidSliceFindingsError(message)
        try:
            validate_audit_v3_slice_report(
                canonical,
                audit_slice=planned[0],
                plan=plan,
            )
        except ValueError as error:
            message = (
                f"Grok slice {artifact.slice_id} failed planned coverage: "
                f"{_redacted_validation_error(error)}"
            )
            raise InvalidSliceFindingsError(message) from error
    return canonical


def _bind_deterministic_slice_fields(  # noqa: PLR0913
    payload: object,
    *,
    manifest: AuditWorkerManifest,
    artifact: AuditWorkerSliceArtifact,
    plan: AuditV3Plan | None = None,
    plan_sha256: str,
    coverage_contract_sha256: str,
) -> object:
    """Replace redundant model-authored fields with local contract facts."""
    if not isinstance(payload, dict):
        return payload
    bound = dict(payload)
    bound.update(
        {
            "version": _REVIEW_WORKFLOW_V3,
            "slice_id": artifact.slice_id,
            "slice_sha256": artifact.slice_sha256,
            "source_id": manifest.source_id,
            "assigned_reviewer": manifest.assigned_reviewer,
            "review_model": manifest.assigned_reviewer,
            "source_sha256": manifest.source_sha256,
            "candidate_sha256": manifest.candidate_sha256,
            "plan_sha256": plan_sha256,
            "coverage_contract_sha256": coverage_contract_sha256,
        }
    )
    contract = getattr(manifest, "coverage_contract", None)
    if contract is not None:
        bound["source_eof_line"] = (
            contract.evidence.english.eof_line_number
        )
        bound["candidate_eof_line"] = (
            contract.evidence.chinese.eof_line_number
        )
    if plan is not None:
        planned = tuple(
            audit_slice
            for audit_slice in plan.slices
            if audit_slice.slice_id == artifact.slice_id
        )
        if len(planned) == 1:
            bound["completed_units"] = [
                unit.model_dump(mode="python", by_alias=True)
                for unit in planned[0].coverage_units
            ]
    issues = bound.get("issues")
    if isinstance(issues, (list, tuple)):
        issue_ids: list[str] = []
        issue_severities: list[str] = []
        for issue in issues:
            if not isinstance(issue, dict):
                break
            issue_id = issue.get("issue_id")
            if not isinstance(issue_id, str):
                break
            severity = issue.get("severity")
            if severity not in {"high", "medium", "low"}:
                break
            issue_ids.append(issue_id)
            issue_severities.append(severity)
        else:
            bound["issue_family_checked_issue_ids"] = issue_ids
            bound["verdict"] = (
                "fail"
                if "high" in issue_severities
                else "warn"
                if issue_severities
                else "pass"
            )
    return bound


def _canonicalize_slice_report(
    report: AuditV3SliceReport,
    *,
    source_path: Path,
    candidate_path: Path,
    repair_source_path: Path | None = None,
    repair_candidate_path: Path | None = None,
) -> AuditV3SliceReport:
    """Recover exact excerpts immediately, before a slice enters the cache."""
    try:
        return canonicalize_audit_v3_slice_report(
            report,
            source_path=source_path,
            candidate_path=candidate_path,
            repair_source_path=repair_source_path or source_path,
            repair_candidate_path=repair_candidate_path or candidate_path,
        )
    except (ValidationError, ValueError) as error:
        message = (
            f"Grok slice {report.slice_id} has invalid exact or raw-mapping "
            f"excerpts: {_redacted_validation_error(error)}"
        )
        raise InvalidSliceFindingsError(message) from error


def _build_slice_retry_prompt(
    *,
    original_prompt: str,
    invalid_payload: object,
    validation_error: Exception,
) -> str:
    """Build one deterministic correction prompt without weakening the schema."""
    return (
        f"{original_prompt.rstrip()}\n\n"
        "CORRECTION ATTEMPT 1 OF 1\n"
        "The previous JSON failed local exact-evidence validation:\n"
        f"{_redacted_validation_error(validation_error)}\n\n"
        "Previous invalid JSON:\n"
        f"{json.dumps(invalid_payload, ensure_ascii=False, indent=2)}\n\n"
        "Return one complete corrected JSON object using the original schema. "
        "Preserve every immutable identity, coverage unit, disposition, and "
        "EOF claim. Copy each source_excerpt and candidate_span_text as one "
        "exact contiguous byte-for-byte excerpt from the assigned files, "
        "including punctuation and backslashes. Every source_excerpt must "
        "identify exactly one occurrence in the assigned source file; when a "
        "short source fragment occurs more than once, replace it with a longer "
        "contiguous enclosing sentence or Markdown line that is unique. Copy "
        "raw Markdown syntax rather than rendered link labels or inline-code "
        "text. Every candidate_span_text must likewise identify exactly one "
        "occurrence in the assigned candidate file; if it repeats, expand it "
        "to a longer exact enclosing sentence or Markdown line. Every "
        "candidate_span_text may appear in at most one issue object; when the "
        "previous payload reused one candidate span for related findings, "
        "merge those findings into one issue instead of duplicating the "
        "evidence. Before returning, "
        "verify that every source_excerpt and candidate_span_text has an exact "
        "occurrence count of one in its assigned file. If that cannot be "
        "established, omit the issue. For an issue inside a text, markdown, "
        "md, or plaintext fence, "
        "candidate_span_text must contain only exact inner content and must not "
        "include the opening or closing fence marker. Keep all applicable "
        "issue-family IDs in "
        "issue_family_checked_issue_ids. Omit an unsupported issue rather than "
        "inventing evidence. Do not add commentary.\n"
    )


def _archive_invalid_payload(
    findings_path: Path,
    *,
    attempt: int,
    payload: object,
    error: Exception,
) -> bool:
    path = _invalid_attempt_path(findings_path, attempt)
    if path.is_file():
        return False
    _atomic_json(
        path,
        {
            "validation_error": _redacted_validation_error(error),
            "payload": payload,
        },
    )
    return True


def _invalid_attempt_path(findings_path: Path, attempt: int) -> Path:
    return findings_path.with_name(
        f"{findings_path.stem}.invalid-attempt-{attempt:02d}.json"
    )


def _read_invalid_payload(path: Path) -> object:
    value = path.read_text(encoding="utf-8-sig")
    try:
        return cast("object", json.loads(value))
    except json.JSONDecodeError:
        return value


def _count_invalid_attempts(
    repo_root: Path,
    manifest: AuditWorkerManifest,
) -> int:
    return sum(
        int(_invalid_attempt_path(findings_path, attempt).is_file())
        for artifact in manifest.slices
        for findings_path in (
            resolve_repo_path(repo_root, artifact.findings_path),
        )
        for attempt in (1, 2)
    )


def _redacted_validation_error(error: Exception) -> str:
    return " ".join(str(error).split())[:1000]


def _parse_concatenated_objects(value: str) -> list[dict[str, object]]:
    decoder = json.JSONDecoder()
    offset = 0
    payloads: list[dict[str, object]] = []
    while offset < len(value):
        while offset < len(value) and value[offset].isspace():
            offset += 1
        if offset >= len(value):
            break
        payload, consumed = cast(
            "tuple[object, int]",
            decoder.raw_decode(value[offset:]),
        )
        if not isinstance(payload, dict):
            message = "Grok CLI emitted a non-object schema payload"
            raise TypeError(message)
        payloads.append(_JsonObject.model_validate(payload).root)
        offset += consumed
    if not payloads:
        message = "Grok CLI emitted no schema payload"
        raise ValueError(message)
    return payloads


def _find_grok() -> str:
    command = shutil.which("grok.exe") or shutil.which("grok")
    if command:
        return command
    fallback = Path.home() / ".grok" / "bin" / "grok.exe"
    if fallback.is_file():
        return str(fallback)
    message = "Local Grok CLI was not found"
    raise FileNotFoundError(message)


def _relative(repo_root: Path, path: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def _atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        _ = temporary.write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        _ = temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _atomic_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        _ = temporary.write_text(
            value,
            encoding="utf-8",
            newline="\n",
        )
        _ = temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _write_status(path: Path, status: GrokAuditWorkerStatus) -> None:
    _atomic_json(path, status.model_dump(mode="json"))


app = typer.Typer(
    help="Run one assigned Grok deep audit.",
    no_args_is_help=True,
)


@app.command("run")
def run_command(
    worker_manifest: Annotated[
        Path,
        typer.Option(
            "--worker-manifest",
            exists=True,
            dir_okay=False,
            resolve_path=True,
        ),
    ],
    repo_root: Annotated[
        Path,
        typer.Option(
            "--repo-root",
            exists=True,
            file_okay=False,
            resolve_path=True,
        ),
    ] = _DEFAULT_REPO_ROOT,
    pipeline_root: Annotated[
        Path,
        typer.Option(
            "--pipeline-root",
            file_okay=False,
            resolve_path=True,
        ),
    ] = _DEFAULT_PIPELINE_ROOT,
    heartbeat_seconds: Annotated[
        float,
        typer.Option("--heartbeat-seconds", min=1.0, max=300.0),
    ] = 45.0,
    timeout_seconds: Annotated[
        float,
        typer.Option("--timeout-seconds", min=60.0, max=7200.0),
    ] = 45.0 * 60.0,
) -> None:
    """Run one lease-bound Grok review without exposing session proxy values."""
    try:
        completion = run_grok_audit_worker(
            worker_manifest_path=worker_manifest,
            repo_root=repo_root,
            pipeline_root=pipeline_root,
            heartbeat_seconds=heartbeat_seconds,
            timeout_seconds=timeout_seconds,
        )
    except Exception as error:
        _ = sys.stderr.write(
            f"Grok audit failed: {type(error).__name__}\n"
        )
        raise typer.Exit(code=1) from error
    _ = sys.stdout.write(completion.model_dump_json() + "\n")


def main() -> int:
    """Run the CLI entry point without exposing proxy or credential values."""
    command = typer.main.get_command(app)
    command(prog_name="scripts.ai.grok_audit_worker")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
