# Copyright 2026
# ruff: noqa: INP001, S101

"""Tests for the Grok v2 deep-audit CLI adapter."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from scripts.ai.audit_v3 import (
    AuditV3Plan,
    AuditV3Slice,
    AuditV3SliceReport,
    CoverageUnit,
)
from scripts.ai.audit_worker import (
    AuditWorkerManifest,
    AuditWorkerSliceArtifact,
)
from scripts.ai.grok_audit_worker import (
    InvalidSliceFindingsError,
    _build_slice_retry_prompt,
    _canonicalize_slice_report,
    _is_final_report_contract_error,
    _load_or_run_valid_slice,
    parse_grok_cli_output,
)

if TYPE_CHECKING:
    from pathlib import Path

_HASH_A = "a" * 64
_HASH_B = "b" * 64
_HASH_C = "c" * 64
_HASH_D = "d" * 64


def _slice_report(
    *,
    source_excerpt: str = "Alpha beta",
    candidate_span_text: str = "中文 片段",
) -> AuditV3SliceReport:
    return AuditV3SliceReport.model_validate(
        {
            "version": 3,
            "plan_sha256": _HASH_A,
            "slice_id": "semantic-01",
            "slice_sha256": _HASH_B,
            "coverage_contract_sha256": _HASH_C,
            "source_id": "codex/test",
            "assigned_reviewer": "grok-4.5",
            "review_model": "grok-4.5",
            "source_sha256": _HASH_D,
            "candidate_sha256": _HASH_A,
            "source_eof_line": 2,
            "candidate_eof_line": 1,
            "verdict": "warn",
            "completed_units": [
                {
                    "section_id": "preamble",
                    "pass": "semantic",
                }
            ],
            "reached_assigned_slice_end": True,
            "reached_real_eof": False,
            "issue_family_sweep_completed": True,
            "issue_family_checked_issue_ids": ["semantic-spacing"],
            "mandatory_evidence_dispositions": [],
            "issues": [
                {
                    "issue_id": "semantic-spacing",
                    "pass": "semantic",
                    "category": "semantic_roles",
                    "section_id": "preamble",
                    "severity": "low",
                    "location": "preamble",
                    "source_excerpt": source_excerpt,
                    "candidate_span_text": candidate_span_text,
                    "explanation": "The evidence must be exact.",
                }
            ],
        }
    )


def test_parse_grok_cli_output_accepts_one_object() -> None:
    """A single successful Grok envelope yields its one report object."""
    payload, ignored = parse_grok_cli_output(
        json.dumps(
            {
                "stopReason": "end_turn",
                "text": {"version": 2, "verdict": "pass"},
            }
        )
    )

    assert payload == {"version": 2, "verdict": "pass"}
    assert ignored == 0


def test_parse_grok_cli_output_prefers_structured_output() -> None:
    """Schema output wins over concatenated textual transport chatter."""
    payload, ignored = parse_grok_cli_output(
        json.dumps(
            {
                "stopReason": "EndTurn",
                "structuredOutput": {"version": 3, "verdict": "warn"},
                "text": '{"draft":1}{"draft":2}',
            }
        )
    )

    assert payload == {"version": 3, "verdict": "warn"}
    assert ignored == 0


def test_parse_grok_cli_output_uses_last_concatenated_object() -> None:
    """Transport chatter is ignored in favor of the last complete object."""
    payload, ignored = parse_grok_cli_output(
        json.dumps(
            {
                "stopReason": "end_turn",
                "text": (
                    '{"version":2,"verdict":"warn"}\n'
                    '{"version":2,"verdict":"pass"}'
                ),
            }
        )
    )

    assert payload == {"version": 2, "verdict": "pass"}
    assert ignored == 1


def test_parse_grok_cli_output_rejects_failed_stop_reason() -> None:
    """A failed Grok stop reason cannot masquerade as a completed review."""
    with pytest.raises(ValueError, match="stopped"):
        _ = parse_grok_cli_output(
            json.dumps(
                {
                    "stopReason": "failed",
                    "text": {"version": 2, "verdict": "pass"},
                }
            )
        )


def test_only_conflicting_issue_spans_are_final_report_contract_errors() -> None:
    """Model id collisions are terminal without hiding unrelated failures."""
    assert _is_final_report_contract_error(
        ValueError("issue id duplicate refers to conflicting exact spans")
    )
    assert not _is_final_report_contract_error(
        ValueError("Grok worker manifest does not own the active audit lease")
    )


def test_slice_validation_recovers_unique_markdown_whitespace(
    tmp_path: Path,
) -> None:
    """A slice is canonicalized before its result becomes reusable cache."""
    source_path = tmp_path / "en.md"
    candidate_path = tmp_path / "zh-CN.md"
    _ = source_path.write_text(
        "Alpha   beta\nGamma\n",
        encoding="utf-8",
        newline="\n",
    )
    _ = candidate_path.write_text(
        "中文   片段\n",
        encoding="utf-8",
        newline="\n",
    )

    canonical = _canonicalize_slice_report(
        _slice_report(),
        source_path=source_path,
        candidate_path=candidate_path,
    )

    assert canonical.issues[0].source_excerpt == "Alpha   beta"
    assert canonical.issues[0].candidate_span_text == "中文   片段"


def test_slice_validation_rejects_nonexistent_exact_excerpt(
    tmp_path: Path,
) -> None:
    """Unsupported evidence is rejected at the slice boundary."""
    source_path = tmp_path / "en.md"
    candidate_path = tmp_path / "zh-CN.md"
    _ = source_path.write_text("Alpha beta\n", encoding="utf-8")
    _ = candidate_path.write_text("中文片段\n", encoding="utf-8")

    with pytest.raises(
        InvalidSliceFindingsError,
        match="candidate_span_text",
    ):
        _ = _canonicalize_slice_report(
            _slice_report(candidate_span_text="不存在"),
            source_path=source_path,
            candidate_path=candidate_path,
        )


def test_slice_validation_rejects_public_unique_raw_duplicate(
    tmp_path: Path,
) -> None:
    """Raw repair ambiguity is corrected before a slice enters the cache."""
    source_path = tmp_path / "public-en.md"
    candidate_path = tmp_path / "public-zh-CN.md"
    repair_source_path = tmp_path / "raw-en.md"
    repair_candidate_path = tmp_path / "raw-zh-CN.md"
    _ = source_path.write_text("Alpha beta\n", encoding="utf-8")
    _ = candidate_path.write_text("时间轴\n", encoding="utf-8")
    _ = repair_source_path.write_text("Alpha beta\n", encoding="utf-8")
    _ = repair_candidate_path.write_text(
        "标题: 时间轴\n正文: 时间轴\n",
        encoding="utf-8",
    )

    with pytest.raises(
        InvalidSliceFindingsError,
        match="not unique in the raw candidate",
    ):
        _ = _canonicalize_slice_report(
            _slice_report(
                source_excerpt="Alpha beta",
                candidate_span_text="时间轴",
            ),
            source_path=source_path,
            candidate_path=candidate_path,
            repair_source_path=repair_source_path,
            repair_candidate_path=repair_candidate_path,
        )


def test_slice_validation_accepts_deterministic_raw_fragment_mapping(
    tmp_path: Path,
) -> None:
    """A localized same-page fragment remains repairable and cacheable."""
    source_path = tmp_path / "public-en.md"
    candidate_path = tmp_path / "public-zh-CN.md"
    repair_source_path = tmp_path / "raw-en.md"
    repair_candidate_path = tmp_path / "raw-zh-CN.md"
    _ = source_path.write_text("Alpha beta\n", encoding="utf-8")
    _ = candidate_path.write_text(
        "参见 [时间轴](#时间轴)。\n",
        encoding="utf-8",
    )
    _ = repair_source_path.write_text("Alpha beta\n", encoding="utf-8")
    _ = repair_candidate_path.write_text(
        "参见 [时间轴](#timeline)。\n",
        encoding="utf-8",
    )

    canonical = _canonicalize_slice_report(
        _slice_report(
            source_excerpt="Alpha beta",
            candidate_span_text="参见 [时间轴](#时间轴)。",
        ),
        source_path=source_path,
        candidate_path=candidate_path,
        repair_source_path=repair_source_path,
        repair_candidate_path=repair_candidate_path,
    )

    assert canonical.issues[0].candidate_span_text == (
        "参见 [时间轴](#时间轴)。"
    )
def test_slice_retry_prompt_is_bounded_and_preserves_invalid_payload() -> None:
    """The correction request keeps the original task and exact failure."""
    prompt = _build_slice_retry_prompt(
        original_prompt="ORIGINAL IMMUTABLE TASK\n",
        invalid_payload={"issue_id": "bad-excerpt", "source_excerpt": "x"},
        validation_error=InvalidSliceFindingsError(
            "source_excerpt is not exact"
        ),
    )

    assert "ORIGINAL IMMUTABLE TASK" in prompt
    assert "CORRECTION ATTEMPT 1 OF 1" in prompt
    assert '"issue_id": "bad-excerpt"' in prompt
    assert "source_excerpt is not exact" in prompt
    assert "byte-for-byte" in prompt
    assert "source_excerpt must identify exactly one occurrence" in prompt
    assert "raw Markdown syntax rather than rendered link labels" in prompt
    assert "candidate_span_text must likewise identify exactly one" in prompt
    assert "candidate_span_text may appear in at most one issue object" in prompt
    assert "merge those findings into one issue" in prompt
    assert "exact occurrence count of one in its assigned file" in prompt
    assert "If that cannot be established, omit the issue" in prompt
    assert "must not include the opening or closing fence marker" in prompt
    assert "Omit an unsupported issue rather than inventing evidence" in prompt


def test_invalid_cached_slice_retries_only_that_slice_once(
    tmp_path: Path,
) -> None:
    """A reusable cache avoids rerunning the original prompt or other slices."""
    source_path = tmp_path / "en.md"
    candidate_path = tmp_path / "zh-CN.md"
    prompt_path = tmp_path / "prompt.txt"
    findings_path = tmp_path / "semantic-01.findings.json"
    _ = source_path.write_text("Alpha beta\n", encoding="utf-8")
    _ = candidate_path.write_text("中文片段\n", encoding="utf-8")
    _ = prompt_path.write_text("ORIGINAL TASK\n", encoding="utf-8")
    invalid = _slice_report(candidate_span_text="不存在")
    _ = findings_path.write_text(
        invalid.model_dump_json(indent=2, by_alias=True),
        encoding="utf-8",
    )
    artifact = AuditWorkerSliceArtifact(
        slice_id="semantic-01",
        slice_sha256=_HASH_B,
        prompt_path="prompt.txt",
        prompt_sha256=_HASH_A,
        schema_path="schema.json",
        schema_sha256=_HASH_A,
        findings_path="semantic-01.findings.json",
        status_path="status.json",
    )
    manifest = AuditWorkerManifest.model_construct(
        source_id="codex/test",
        assigned_reviewer="grok-4.5",
        source_sha256=_HASH_D,
        candidate_sha256=_HASH_A,
    )
    prompts: list[Path] = []

    def invoke(
        retry_prompt_path: Path,
        _stdout_path: Path,
        _stderr_path: Path,
    ) -> dict[str, object]:
        prompts.append(retry_prompt_path)
        return _slice_report(
            source_excerpt="Alpha beta",
            candidate_span_text="中文片段",
        ).model_dump(mode="python", by_alias=True)

    corrected, invalid_attempts = _load_or_run_valid_slice(
        manifest=manifest,
        artifact=artifact,
        plan_sha256=_HASH_A,
        coverage_contract_sha256=_HASH_C,
        findings_path=findings_path,
        source_path=source_path,
        candidate_path=candidate_path,
        original_prompt_path=prompt_path,
        original_stdout_path=tmp_path / "stdout.json",
        original_stderr_path=tmp_path / "stderr.log",
        invoke=invoke,
    )

    assert corrected.issues[0].candidate_span_text == "中文片段"
    assert invalid_attempts == 1
    assert len(prompts) == 1
    assert prompts[0].name.endswith(".retry-01.txt")
    assert (tmp_path / "semantic-01.findings.invalid-attempt-01.json").is_file()
    assert not (
        tmp_path / "semantic-01.findings.invalid-attempt-02.json"
    ).exists()


def test_planned_units_are_bound_locally_at_slice_boundary(
    tmp_path: Path,
) -> None:
    """Bind plan-owned coverage units before final report merging."""
    source_path = tmp_path / "en.md"
    candidate_path = tmp_path / "zh-CN.md"
    prompt_path = tmp_path / "prompt.txt"
    findings_path = tmp_path / "semantic-01.findings.json"
    _ = source_path.write_text("Alpha beta\n", encoding="utf-8")
    _ = candidate_path.write_text("candidate text\n", encoding="utf-8")
    _ = prompt_path.write_text("ORIGINAL TASK\n", encoding="utf-8")
    incomplete = _slice_report(candidate_span_text="candidate text")
    _ = findings_path.write_text(
        incomplete.model_dump_json(indent=2, by_alias=True),
        encoding="utf-8",
    )
    first_unit = incomplete.completed_units[0]
    second_unit = CoverageUnit.model_validate(
        {"section_id": "section-0002-abcdefabcdef", "pass": "semantic"}
    )
    planned_slice = AuditV3Slice.model_construct(
        slice_id="semantic-01",
        slice_sha256=_HASH_B,
        role="semantic",
        coverage_units=(first_unit, second_unit),
        mandatory_evidence_ids=(),
    )
    plan = AuditV3Plan.model_construct(
        plan_sha256=_HASH_A,
        coverage_contract_sha256=_HASH_C,
        source_id="codex/test",
        assigned_reviewer="grok-4.5",
        source_sha256=_HASH_D,
        candidate_sha256=_HASH_A,
        source_eof_line=2,
        candidate_eof_line=1,
        slices=(planned_slice,),
    )
    artifact = AuditWorkerSliceArtifact(
        slice_id="semantic-01",
        slice_sha256=_HASH_B,
        prompt_path="prompt.txt",
        prompt_sha256=_HASH_A,
        schema_path="schema.json",
        schema_sha256=_HASH_A,
        findings_path="semantic-01.findings.json",
        status_path="status.json",
    )
    manifest = AuditWorkerManifest.model_construct(
        source_id="codex/test",
        assigned_reviewer="grok-4.5",
        source_sha256=_HASH_D,
        candidate_sha256=_HASH_A,
    )
    prompts: list[Path] = []

    def invoke(
        retry_prompt_path: Path,
        _stdout_path: Path,
        _stderr_path: Path,
    ) -> dict[str, object]:
        prompts.append(retry_prompt_path)
        return incomplete.model_dump(mode="python", by_alias=True)

    corrected, invalid_attempts = _load_or_run_valid_slice(
        manifest=manifest,
        artifact=artifact,
        plan=plan,
        plan_sha256=_HASH_A,
        coverage_contract_sha256=_HASH_C,
        findings_path=findings_path,
        source_path=source_path,
        candidate_path=candidate_path,
        original_prompt_path=prompt_path,
        original_stdout_path=tmp_path / "stdout.json",
        original_stderr_path=tmp_path / "stderr.log",
        invoke=invoke,
    )

    assert corrected.completed_units == (first_unit, second_unit)
    assert invalid_attempts == 0
    assert prompts == []


def test_cached_slice_identity_is_bound_without_model_retry(
    tmp_path: Path,
) -> None:
    """Immutable identity is recovered locally instead of asking the model."""
    source_path = tmp_path / "en.md"
    candidate_path = tmp_path / "zh-CN.md"
    prompt_path = tmp_path / "prompt.txt"
    findings_path = tmp_path / "semantic-01.findings.json"
    _ = source_path.write_text("Alpha beta\n", encoding="utf-8")
    _ = candidate_path.write_text("candidate text\n", encoding="utf-8")
    _ = prompt_path.write_text("ORIGINAL TASK\n", encoding="utf-8")
    invalid = _slice_report(
        candidate_span_text="candidate text"
    ).model_dump(mode="python", by_alias=True)
    invalid["plan_sha256"] = _HASH_D
    invalid["candidate_sha256"] = _HASH_D
    invalid["coverage_contract_sha256"] = _HASH_D
    _ = findings_path.write_text(
        json.dumps(invalid, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    artifact = AuditWorkerSliceArtifact(
        slice_id="semantic-01",
        slice_sha256=_HASH_B,
        prompt_path="prompt.txt",
        prompt_sha256=_HASH_A,
        schema_path="schema.json",
        schema_sha256=_HASH_A,
        findings_path="semantic-01.findings.json",
        status_path="status.json",
    )
    manifest = AuditWorkerManifest.model_construct(
        source_id="codex/test",
        assigned_reviewer="grok-4.5",
        source_sha256=_HASH_D,
        candidate_sha256=_HASH_A,
        v3_plan_sha256=_HASH_C,
    )
    prompts: list[Path] = []

    def invoke(
        retry_prompt_path: Path,
        _stdout_path: Path,
        _stderr_path: Path,
    ) -> dict[str, object]:
        prompts.append(retry_prompt_path)
        return _slice_report(
            candidate_span_text="candidate text"
        ).model_dump(mode="python", by_alias=True)

    corrected, invalid_attempts = _load_or_run_valid_slice(
        manifest=manifest,
        artifact=artifact,
        plan_sha256=_HASH_B,
        coverage_contract_sha256=_HASH_C,
        findings_path=findings_path,
        source_path=source_path,
        candidate_path=candidate_path,
        original_prompt_path=prompt_path,
        original_stdout_path=tmp_path / "stdout.json",
        original_stderr_path=tmp_path / "stderr.log",
        invoke=invoke,
    )

    assert corrected.candidate_sha256 == _HASH_A
    assert corrected.plan_sha256 == _HASH_B
    assert corrected.coverage_contract_sha256 == _HASH_C
    assert invalid_attempts == 0
    assert prompts == []
    assert not (
        tmp_path / "semantic-01.findings.invalid-attempt-01.json"
    ).exists()


def test_derived_issue_family_ids_are_bound_without_model_retry(
    tmp_path: Path,
) -> None:
    """A redundant issue-id list cannot waste the bounded correction call."""
    source_path = tmp_path / "en.md"
    candidate_path = tmp_path / "zh-CN.md"
    prompt_path = tmp_path / "prompt.txt"
    findings_path = tmp_path / "semantic-01.findings.json"
    _ = source_path.write_text("Alpha beta\n", encoding="utf-8")
    _ = candidate_path.write_text("candidate text\n", encoding="utf-8")
    _ = prompt_path.write_text("ORIGINAL TASK\n", encoding="utf-8")
    artifact = AuditWorkerSliceArtifact(
        slice_id="semantic-01",
        slice_sha256=_HASH_B,
        prompt_path="prompt.txt",
        prompt_sha256=_HASH_A,
        schema_path="schema.json",
        schema_sha256=_HASH_A,
        findings_path="semantic-01.findings.json",
        status_path="status.json",
    )
    manifest = AuditWorkerManifest.model_construct(
        source_id="codex/test",
        assigned_reviewer="grok-4.5",
        source_sha256=_HASH_D,
        candidate_sha256=_HASH_A,
    )
    prompts: list[Path] = []

    def invoke(
        prompt: Path,
        _stdout_path: Path,
        _stderr_path: Path,
    ) -> dict[str, object]:
        prompts.append(prompt)
        payload = _slice_report(
            candidate_span_text="candidate text"
        ).model_dump(mode="python", by_alias=True)
        payload["issue_family_checked_issue_ids"] = []
        payload["source_id"] = "wrong/source"
        payload["source_sha256"] = _HASH_B
        return payload

    corrected, invalid_attempts = _load_or_run_valid_slice(
        manifest=manifest,
        artifact=artifact,
        plan_sha256=_HASH_A,
        coverage_contract_sha256=_HASH_C,
        findings_path=findings_path,
        source_path=source_path,
        candidate_path=candidate_path,
        original_prompt_path=prompt_path,
        original_stdout_path=tmp_path / "stdout.json",
        original_stderr_path=tmp_path / "stderr.log",
        invoke=invoke,
    )

    assert corrected.source_id == "codex/test"
    assert corrected.source_sha256 == _HASH_D
    assert corrected.issue_family_checked_issue_ids == ("semantic-spacing",)
    assert invalid_attempts == 0
    assert prompts == [prompt_path]
    assert not (
        tmp_path / "semantic-01.findings.invalid-attempt-01.json"
    ).exists()


def test_derived_verdict_is_bound_without_model_retry(
    tmp_path: Path,
) -> None:
    """Issue severities, not a redundant model verdict, drive the schema."""
    source_path = tmp_path / "en.md"
    candidate_path = tmp_path / "zh-CN.md"
    prompt_path = tmp_path / "prompt.txt"
    findings_path = tmp_path / "semantic-01.findings.json"
    _ = source_path.write_text("Alpha beta\n", encoding="utf-8")
    _ = candidate_path.write_text("candidate text\n", encoding="utf-8")
    _ = prompt_path.write_text("ORIGINAL TASK\n", encoding="utf-8")
    artifact = AuditWorkerSliceArtifact(
        slice_id="semantic-01",
        slice_sha256=_HASH_B,
        prompt_path="prompt.txt",
        prompt_sha256=_HASH_A,
        schema_path="schema.json",
        schema_sha256=_HASH_A,
        findings_path="semantic-01.findings.json",
        status_path="status.json",
    )
    manifest = AuditWorkerManifest.model_construct(
        source_id="codex/test",
        assigned_reviewer="grok-4.5",
        source_sha256=_HASH_D,
        candidate_sha256=_HASH_A,
    )
    prompts: list[Path] = []

    def invoke(
        prompt: Path,
        _stdout_path: Path,
        _stderr_path: Path,
    ) -> dict[str, object]:
        prompts.append(prompt)
        payload = _slice_report(
            candidate_span_text="candidate text"
        ).model_dump(mode="python", by_alias=True)
        payload["verdict"] = "fail"
        return payload

    corrected, invalid_attempts = _load_or_run_valid_slice(
        manifest=manifest,
        artifact=artifact,
        plan_sha256=_HASH_A,
        coverage_contract_sha256=_HASH_C,
        findings_path=findings_path,
        source_path=source_path,
        candidate_path=candidate_path,
        original_prompt_path=prompt_path,
        original_stdout_path=tmp_path / "stdout.json",
        original_stderr_path=tmp_path / "stderr.log",
        invoke=invoke,
    )

    assert corrected.verdict == "warn"
    assert invalid_attempts == 0
    assert prompts == [prompt_path]
    assert not (
        tmp_path / "semantic-01.findings.invalid-attempt-01.json"
    ).exists()
