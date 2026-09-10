# Copyright 2026
# ruff: noqa: INP001, S101

"""Tests for content-evidence recovery of historical audit issues."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, cast

from scripts.ai.audit_history import recover_audit_history

if TYPE_CHECKING:
    from pathlib import Path

    from scripts.ai.audit_history import AuditHistoryRecovery


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, str):
        _ = path.write_text(value, encoding="utf-8", newline="\n")
        return
    _ = path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
        newline="\n",
    )


def _report(
    source_id: str,
    reviewer: str,
    issues: list[dict[str, object]],
    *,
    source_sha256: str = "0" * 64,
    candidate_sha256: str = "1" * 64,
) -> dict[str, object]:
    return {
        "source_id": source_id,
        "review_model": reviewer,
        "verdict": "fail",
        "source_sha256": source_sha256,
        "candidate_sha256": candidate_sha256,
        "issues": issues,
    }


def _issue(
    *,
    severity: str = "high",
    source_excerpt: str = "The source sentence is stable.",
    candidate_excerpt: str = "译文句子仍然存在。",
) -> dict[str, object]:
    return {
        "issue_id": "semantic-01",
        "severity": severity,
        "category": "semantic",
        "location": "Section one",
        "source_excerpt": source_excerpt,
        "candidate_span_text": candidate_excerpt,
        "explanation": "The relationship is reversed.",
    }


def _recover(tmp_path: Path, *, include_low: bool = False) -> AuditHistoryRecovery:
    english = tmp_path / "site/en.md"
    chinese = tmp_path / "site/zh-CN.md"
    _write(english, "# English\n\nThe source sentence is stable.\n")
    _write(chinese, "# Chinese\n\n译文句子仍然存在。\n")
    return recover_audit_history(
        repo_root=tmp_path,
        source_id="codex/example",
        assigned_reviewer="gpt-5.6-terra",
        english_path=english,
        english_text=english.read_text(encoding="utf-8"),
        chinese_path=chinese,
        chinese_text=chinese.read_text(encoding="utf-8"),
        history_root=tmp_path / ".ai-local/reviews",
        include_low=include_low,
    )


def test_hash_change_does_not_discard_content_still_present(tmp_path: Path) -> None:
    """Current text evidence carries an issue forward despite stale page hashes."""
    _write(
        tmp_path / ".ai-local/reviews/old/report.json",
        _report("codex/example", "gpt-5.6-terra", [_issue()]),
    )
    recovered = _recover(tmp_path)
    assert recovered.english_sha256 != "0" * 64
    assert recovered.chinese_sha256 != "1" * 64
    assert recovered.accepted_report_count == 1
    assert recovered.issues[0].disposition == "carry-forward"
    assert recovered.issues[0].source_match is not None
    assert recovered.issues[0].candidate_match is not None


def test_duplicate_reports_deduplicate_by_semantics_and_candidate_span(tmp_path: Path) -> None:
    """Equivalent issue evidence from two reports becomes one deterministic recovery."""
    report = _report("codex/example", "gpt-5.6-terra", [_issue()])
    alternate = _report("codex/example", "gpt-5.6-terra", [_issue()])
    alternate_issue = cast(
        "dict[str, object]",
        cast("list[object]", alternate["issues"])[0],
    )
    alternate_issue["english_excerpt"] = alternate_issue.pop("source_excerpt")
    alternate_issue["chinese_excerpt"] = alternate_issue.pop("candidate_span_text")
    third = _report("codex/example", "gpt-5.6-terra", [_issue()])
    third_issue = cast(
        "dict[str, object]",
        cast("list[object]", third["issues"])[0],
    )
    third_issue["source_span_text"] = third_issue.pop("source_excerpt")
    third_issue["candidate_excerpt"] = third_issue.pop("candidate_span_text")
    _write(tmp_path / ".ai-local/reviews/z-last/report.json", report)
    _write(tmp_path / ".ai-local/reviews/a-first/report.json", report)
    _write(tmp_path / ".ai-local/reviews/middle/report.json", alternate)
    _write(tmp_path / ".ai-local/reviews/third/report.json", third)
    recovered = _recover(tmp_path)
    assert len(recovered.issues) == 1
    references = recovered.issues[0].source_reports
    assert [reference.report_path for reference in references] == [
        ".ai-local/reviews/a-first/report.json",
        ".ai-local/reviews/middle/report.json",
        ".ai-local/reviews/third/report.json",
        ".ai-local/reviews/z-last/report.json",
    ]


def test_reviewer_mismatch_is_filtered_without_cross_reviewer_recovery(tmp_path: Path) -> None:
    """A Grok report cannot seed a Terra-assigned page's repair evidence."""
    _write(
        tmp_path / ".ai-local/reviews/grok/report.json",
        _report("codex/example", "grok-4.5", [_issue()]),
    )
    recovered = _recover(tmp_path)
    assert recovered.accepted_report_count == 0
    assert recovered.issues == ()
    assert recovered.rejected_reports[0].reason == "assigned-reviewer-mismatch"


def test_explicit_invalidation_ledger_prevents_rejected_report_revival(
    tmp_path: Path,
) -> None:
    """An explicit invalidation ledger wins over an otherwise valid report."""
    report_path = tmp_path / ".ai-local/reviews/old/report.json"
    _write(
        report_path,
        _report("codex/example", "gpt-5.6-terra", [_issue()]),
    )
    _write(
        tmp_path / ".ai-local/rejected-reviews/old-invalid/report.json",
        {
            "kind": "invalid-review-record",
            "status": "invalid",
            "source_id": "codex/example",
            "review_model": "gpt-5.6-terra",
            "invalidated_report_path": report_path.relative_to(tmp_path).as_posix(),
            "reason": "The original reviewer did not reach the real EOF.",
        },
    )

    recovered = _recover(tmp_path)

    assert recovered.accepted_report_count == 0
    assert recovered.issues == ()
    assert recovered.rejected_reports[0].report_path == (
        ".ai-local/reviews/old/report.json"
    )
    assert recovered.rejected_reports[0].reason.startswith(
        "invalidated-by-ledger:"
    )


def test_missing_source_excerpt_is_marked_not_present_after_source_change(tmp_path: Path) -> None:
    """A disappeared English excerpt is not revived merely because Chinese text remains."""
    issue = _issue(source_excerpt="This sentence no longer exists.")
    _write(
        tmp_path / ".ai-local/reviews/report.json",
        _report("codex/example", "gpt-5.6-terra", [issue]),
    )
    recovered = _recover(tmp_path)
    assert recovered.issues[0].disposition == "not-present-after-source-change"
    assert recovered.issues[0].source_match is None
    assert recovered.issues[0].candidate_match is not None


def test_low_severity_policy_is_opt_in_and_whitespace_recovery_is_safe(tmp_path: Path) -> None:
    """Low issues need an explicit policy and recover only a unique whitespace variant."""
    english = tmp_path / "site/en.md"
    chinese = tmp_path / "site/zh-CN.md"
    _write(english, "# English\n\nThe source sentence\n is stable.\n")
    _write(chinese, "# Chinese\n\n译文句子\n仍然存在。\n")
    _write(
        tmp_path / ".ai-local/reviews/report.json",
        _report(
            "codex/example",
            "gpt-5.6-terra",
            [
                _issue(
                    severity="low",
                    source_excerpt="The source sentence is stable.",
                    candidate_excerpt="译文句子仍然存在。",
                )
            ],
        ),
    )
    default = recover_audit_history(
        repo_root=tmp_path,
        source_id="codex/example",
        assigned_reviewer="gpt-5.6-terra",
        english_path=english,
        english_text=english.read_text(encoding="utf-8"),
        chinese_path=chinese,
        chinese_text=chinese.read_text(encoding="utf-8"),
        history_root=tmp_path / ".ai-local/reviews",
    )
    included = recover_audit_history(
        repo_root=tmp_path,
        source_id="codex/example",
        assigned_reviewer="gpt-5.6-terra",
        english_path=english,
        english_text=english.read_text(encoding="utf-8"),
        chinese_path=chinese,
        chinese_text=chinese.read_text(encoding="utf-8"),
        history_root=tmp_path / ".ai-local/reviews",
        include_low=True,
    )
    assert default.issues == ()
    assert included.issues[0].disposition == "carry-forward"
    assert included.issues[0].source_match is not None
    assert included.issues[0].source_match.match_kind == "whitespace"
    assert included.issues[0].candidate_match is not None
    assert included.issues[0].candidate_match.match_kind == "whitespace"


def test_legacy_severity_and_issue_id_aliases_are_recovered(
    tmp_path: Path,
) -> None:
    """Older fail/warn/minor reports remain usable as current content evidence."""
    issues = [
        {
            **_issue(severity=severity),
            "id": f"legacy-{severity}",
        }
        for severity in ("fail", "warn", "minor")
    ]
    for issue in issues:
        _ = issue.pop("issue_id")
    _write(
        tmp_path / ".ai-local/reviews/legacy/report.json",
        _report("codex/example", "gpt-5.6-terra", issues),
    )

    recovered = _recover(tmp_path, include_low=True)

    assert {item.severity for item in recovered.issues} == {
        "high",
        "medium",
        "low",
    }
    assert {
        reference.issue_id
        for item in recovered.issues
        for reference in item.source_reports
    } == {"legacy-fail", "legacy-warn", "legacy-minor"}
