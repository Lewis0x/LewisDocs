# Copyright 2026
# ruff: noqa: INP001, PLR2004, S101

"""Tests for conserved audit inventory and controlled pilot admission."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.ai.audit_inventory import (
    AuditInventory,
    CanonicalSourceState,
    InventorySource,
    InventoryStatus,
    ReviewScan,
    ReviewSourceEvidence,
    build_inventory,
    build_inventory_from_sources,
    scan_review_evidence,
    select_pilot,
    stable_reviewer,
    write_inventory_atomic,
)

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_HASH = "f" * 64
CONTENT_HASH = "a" * 64


def _write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(value, encoding="utf-8", newline="\n")


def _source(source_id: str) -> InventorySource:
    product = "claude-code" if source_id.startswith("claude-code/") else "codex"
    return InventorySource(
        source_id=source_id,
        product=product,
        title=f"Title for {source_id}",
    )


def _page(
    source: InventorySource,
    *,
    language: str,
    detail_repetitions: int = 20,
    translation_model: str = "k3",
) -> str:
    common = (
        "---\n"
        f"title: {source.title}\n"
        f"source_id: {source.source_id}\n"
        f"product: {source.product}\n"
        f"lang: {language}\n"
        f"canonical_url: https://example.test/{source.source_id}\n"
        "owner: OpenAI\n"
        f"content_sha256: {CONTENT_HASH}\n"
    )
    if language == "zh-CN":
        common += (
            f"translation_of: {source.source_id}\n"
            f"translation_model: {translation_model}\n"
            "ai_translated: true\n"
        )
    detail = "detail " * detail_repetitions
    return f"{common}---\n# {source.title}\n\n## Details\n\n{detail}\n"


def _install_pair(
    root: Path,
    source: InventorySource,
    *,
    detail_repetitions: int = 20,
    translation_model: str = "k3",
) -> tuple[Path, Path]:
    english = root / f"source-ai/content/en/{source.source_id}.md"
    chinese = root / f".ai-local/staging/dual-review-normalized/{source.source_id}.md"
    _write(
        english,
        _page(
            source,
            language="en",
            detail_repetitions=detail_repetitions,
        ),
    )
    _write(
        chinese,
        _page(
            source,
            language="zh-CN",
            detail_repetitions=detail_repetitions,
            translation_model=translation_model,
        ),
    )
    return english, chinese


def _review_scan(
    evidence: tuple[ReviewSourceEvidence, ...],
) -> ReviewScan:
    return ReviewScan(
        files_scanned=len(evidence),
        exact_source_reports=len(evidence),
        ignored_malformed=0,
        ignored_unknown_source=0,
        ignored_without_reviewer=0,
        evidence=evidence,
    )


def _build(
    root: Path,
    sources: tuple[InventorySource, ...],
    *,
    canonical_states: tuple[tuple[str, tuple[CanonicalSourceState, ...]], ...] = (),
    review_scan: ReviewScan | None = None,
    official_ids: tuple[str, ...] = (),
) -> AuditInventory:
    return build_inventory_from_sources(
        root,
        sources,
        manifest_path="source-ai/sources.yaml",
        manifest_sha256=MANIFEST_HASH,
        canonical_states=canonical_states,
        review_scan=review_scan,
        official_verified_source_ids=official_ids,
    )


def test_inventory_classifies_every_current_state_with_strict_precedence(
    tmp_path: Path,
) -> None:
    """Formal, canonical, conflict, isolation, missing, and eligible are exclusive."""
    source_ids = (
        "codex/formal",
        "codex/current",
        "codex/conflict",
        "codex/isolated",
        "codex/missing-source",
        "codex/missing-normalized",
        "codex/assigned",
        "codex/unassigned",
    )
    sources = tuple(_source(source_id) for source_id in source_ids)
    by_id = {source.source_id: source for source in sources}
    for source_id in (
        "codex/formal",
        "codex/current",
        "codex/conflict",
        "codex/isolated",
        "codex/assigned",
        "codex/unassigned",
    ):
        _ = _install_pair(tmp_path, by_id[source_id])
    missing_normalized = by_id["codex/missing-normalized"]
    _write(
        tmp_path / f"source-ai/content/en/{missing_normalized.source_id}.md",
        _page(missing_normalized, language="en"),
    )
    formal_candidate = tmp_path / ".ai-local/staging/dual-review-normalized/codex/formal.md"
    formal_target = tmp_path / "source-ai/content/zh-CN/codex/formal.md"
    formal_target.parent.mkdir(parents=True, exist_ok=True)
    _ = formal_target.write_bytes(formal_candidate.read_bytes())
    current = CanonicalSourceState(
        kind="pipeline",
        record_id="1" * 64,
        state="isolated",
        terminal=True,
        assigned_reviewer="gpt-5.6-terra",
    )
    reviews = _review_scan(
        (
            ReviewSourceEvidence(
                source_id="codex/conflict",
                reviewers=("gpt-5.6-terra", "grok-4.5"),
                reviewer_report_count=2,
            ),
            ReviewSourceEvidence(
                source_id="codex/isolated",
                reviewers=("grok-4.5",),
                reviewer_report_count=1,
                legacy_isolated=True,
                isolated_report_count=1,
            ),
            ReviewSourceEvidence(
                source_id="codex/assigned",
                reviewers=("gpt-5.6-terra",),
                reviewer_report_count=1,
            ),
        )
    )
    inventory = _build(
        tmp_path,
        sources,
        canonical_states=(("codex/current", (current,)),),
        review_scan=reviews,
        official_ids=("codex/unassigned",),
    )
    statuses = {item.source_id: item.status for item in inventory.items}
    assert statuses == {
        "codex/formal": InventoryStatus.FORMAL_VALID,
        "codex/current": InventoryStatus.CURRENT_PIPELINE,
        "codex/conflict": InventoryStatus.REVIEWER_CONFLICT,
        "codex/isolated": InventoryStatus.LEGACY_ISOLATED,
        "codex/missing-source": InventoryStatus.MISSING_SOURCE,
        "codex/missing-normalized": InventoryStatus.MISSING_NORMALIZED,
        "codex/assigned": InventoryStatus.ELIGIBLE_ASSIGNED,
        "codex/unassigned": InventoryStatus.ELIGIBLE_UNASSIGNED,
    }
    items = {item.source_id: item for item in inventory.items}
    assert items["codex/current"].canonical_states == (current,)
    assert items["codex/conflict"].reviewer_conflict
    assert items["codex/conflict"].admission_reviewer is None
    assert items["codex/assigned"].admission_reviewer == "gpt-5.6-terra"
    assert items["codex/unassigned"].admission_reviewer == stable_reviewer("codex/unassigned")
    assert items["codex/unassigned"].official_localization_verified
    assert items["codex/unassigned"].translation_model == "k3"
    assert items["codex/unassigned"].translation_provider == "kimi"
    assert items["codex/unassigned"].english_sha256 is not None
    assert items["codex/unassigned"].normalized_candidate_sha256 is not None
    assert items["codex/unassigned"].english_headings == 2
    assert items["codex/unassigned"].chinese_headings == 2
    assert items["codex/unassigned"].estimated_work_units > 0
    assert sum(inventory.status_counts.values()) == len(sources)
    assert inventory.unknown_source_count == 0


def test_review_scan_uses_only_exact_source_id_and_marks_model_conflict(
    tmp_path: Path,
) -> None:
    """File names and nested references cannot assign or silently reassign a page."""
    reviews = tmp_path / ".ai-local/reviews"
    _write(
        reviews / "terra.json",
        json.dumps(
            {
                "source_id": "codex/exact",
                "review_model": "gpt-5.6-terra",
                "status": "warn",
            }
        ),
    )
    _write(
        reviews / "grok.json",
        json.dumps(
            {
                "source_id": "codex/exact",
                "assigned_reviewer": "grok-4.5",
                "status": "fail",
            }
        ),
    )
    _write(
        reviews / "isolated.json",
        json.dumps(
            {
                "source_id": "codex/isolated",
                "assigned_reviewer": "gpt-5.6-terra",
                "status": "isolated",
            }
        ),
    )
    _write(
        reviews / "unknown.json",
        json.dumps(
            {
                "source_id": "codex/not-in-manifest",
                "review_model": "grok-4.5",
            }
        ),
    )
    _write(
        reviews / "nested-only.json",
        json.dumps(
            {
                "metadata": {
                    "source_id": "codex/exact",
                    "review_model": "grok-4.5",
                }
            }
        ),
    )
    _write(
        reviews / "no-reviewer.json",
        json.dumps({"source_id": "codex/exact", "status": "warn"}),
    )
    _write(reviews / "malformed.json", "{not-json")
    scan = scan_review_evidence(
        tmp_path,
        ("codex/exact", "codex/isolated"),
    )
    evidence = {item.source_id: item for item in scan.evidence}
    assert scan.files_scanned == 7
    assert scan.exact_source_reports == 4
    assert scan.ignored_malformed == 1
    assert scan.ignored_unknown_source == 2
    assert scan.ignored_without_reviewer == 1
    assert evidence["codex/exact"].reviewers == (
        "gpt-5.6-terra",
        "grok-4.5",
    )
    assert evidence["codex/isolated"].legacy_isolated
    assert evidence["codex/isolated"].isolated_report_count == 1


def test_stable_reviewer_assignment_is_order_independent() -> None:
    """Unassigned pages keep the same SHA-256 reviewer across inventory runs."""
    source_ids = tuple(f"codex/stable-{index:02d}" for index in range(40))
    forward = {source_id: stable_reviewer(source_id) for source_id in source_ids}
    reverse = {source_id: stable_reviewer(source_id) for source_id in reversed(source_ids)}
    assert forward == reverse
    assert set(forward.values()) == {"gpt-5.6-terra", "grok-4.5"}


def test_select_pilot_preserves_reviewers_and_balances_default_six_plus_six(
    tmp_path: Path,
) -> None:
    """A single-product pool still selects 6+6 and balances reviewer lanes."""
    terra = tuple(_source(f"codex/terra-{index:02d}") for index in range(12))
    grok = tuple(_source(f"codex/grok-{index:02d}") for index in range(12))
    sources = terra + grok
    for index, source in enumerate(sources, start=1):
        _ = _install_pair(
            tmp_path,
            source,
            detail_repetitions=index * 35,
            translation_model="glm-5.2" if source in grok else "k3",
        )
    evidence = tuple(
        ReviewSourceEvidence(
            source_id=source.source_id,
            reviewers=("gpt-5.6-terra",),
            reviewer_report_count=1,
        )
        for source in terra
    ) + tuple(
        ReviewSourceEvidence(
            source_id=source.source_id,
            reviewers=("grok-4.5",),
            reviewer_report_count=1,
        )
        for source in grok
    )
    inventory = _build(
        tmp_path,
        sources,
        review_scan=_review_scan(evidence),
        official_ids=("codex/terra-00", "codex/grok-00"),
    )
    pilot = select_pilot(inventory)
    assert pilot.selected_count == 12
    assert pilot.reviewer_counts == {
        "gpt-5.6-terra": 6,
        "grok-4.5": 6,
    }
    assert pilot.product_counts == {
        "claude-code": 0,
        "codex": 12,
    }
    selected_ids = {selection.source_id for selection in pilot.selections}
    assert len(selected_ids) == 12
    assert {"codex/terra-00", "codex/grok-00"} <= selected_ids
    excluded_ids = tuple(
        sorted(selection.source_id for selection in pilot.selections[:2])
    )
    replacement_pilot = select_pilot(
        inventory,
        excluded_source_ids=excluded_ids,
    )
    assert replacement_pilot.selected_count == 12
    assert replacement_pilot.excluded_source_ids == excluded_ids
    assert not (
        set(excluded_ids)
        & {selection.source_id for selection in replacement_pilot.selections}
    )
    inventory_by_id = {item.source_id: item for item in inventory.items}
    for selection in pilot.selections:
        assert inventory_by_id[selection.source_id].historical_reviewer == selection.reviewer
    for reviewer in ("gpt-5.6-terra", "grok-4.5"):
        selected_work = sorted(
            (
                selection.estimated_work_units
                for selection in pilot.selections
                if selection.reviewer == reviewer
            ),
            reverse=True,
        )
        expected_loads = [0, 0, 0]
        for work in selected_work:
            lane = min(
                range(3),
                key=lambda index: (expected_loads[index], index),
            )
            expected_loads[lane] += work
        actual_loads = [lane.total_work_units for lane in pilot.lanes if lane.reviewer == reviewer]
        assert actual_loads == expected_loads
        assert max(actual_loads) - min(actual_loads) <= max(selected_work)


def test_select_pilot_stratifies_manifest_products_and_keeps_long_pages(
    tmp_path: Path,
) -> None:
    """The default pilot approximates 172:131 while retaining pressure pages."""
    terra_claude = tuple(_source(f"claude-code/terra-claude-{index:02d}") for index in range(8))
    terra_codex = tuple(_source(f"codex/terra-codex-{index:02d}") for index in range(8))
    grok_claude = tuple(_source(f"claude-code/grok-claude-{index:02d}") for index in range(8))
    grok_codex = tuple(_source(f"codex/grok-codex-{index:02d}") for index in range(8))
    candidates = terra_claude + terra_codex + grok_claude + grok_codex
    filler_claude = tuple(_source(f"claude-code/filler-{index:03d}") for index in range(156))
    filler_codex = tuple(_source(f"codex/filler-{index:03d}") for index in range(115))
    sources = candidates + filler_claude + filler_codex
    terra_long = terra_claude[-1]
    grok_long = grok_codex[-1]
    for index, source in enumerate(candidates, start=1):
        repetitions = index * 20
        if source == terra_long:
            repetitions = 8_000
        if source == grok_long:
            repetitions = 7_000
        _ = _install_pair(
            tmp_path,
            source,
            detail_repetitions=repetitions,
        )
    terra_sources = terra_claude + terra_codex
    grok_sources = grok_claude + grok_codex
    evidence = tuple(
        ReviewSourceEvidence(
            source_id=source.source_id,
            reviewers=("gpt-5.6-terra",),
            reviewer_report_count=1,
        )
        for source in terra_sources
    ) + tuple(
        ReviewSourceEvidence(
            source_id=source.source_id,
            reviewers=("grok-4.5",),
            reviewer_report_count=1,
        )
        for source in grok_sources
    )
    inventory = _build(
        tmp_path,
        sources,
        review_scan=_review_scan(evidence),
        official_ids=(
            terra_codex[0].source_id,
            grok_claude[0].source_id,
        ),
    )
    pilot = select_pilot(inventory)
    assert pilot.manifest_product_counts == {
        "claude-code": 172,
        "codex": 131,
    }
    assert pilot.reviewer_counts == {
        "gpt-5.6-terra": 6,
        "grok-4.5": 6,
    }
    assert pilot.product_targets == {
        "claude-code": 7,
        "codex": 5,
    }
    assert pilot.product_counts == pilot.product_targets
    for reviewer in ("gpt-5.6-terra", "grok-4.5"):
        assert {
            selection.product for selection in pilot.selections if selection.reviewer == reviewer
        } == {"claude-code", "codex"}
    selected_ids = {selection.source_id for selection in pilot.selections}
    assert {terra_long.source_id, grok_long.source_id} <= selected_ids
    assert select_pilot(inventory).model_dump_json() == pilot.model_dump_json()


def test_select_pilot_falls_back_when_reviewer_or_product_candidates_are_short(
    tmp_path: Path,
) -> None:
    """Short lanes admit the nearest feasible mix without reviewer reassignment."""
    terra = (
        _source("claude-code/terra-short-0"),
        _source("claude-code/terra-short-1"),
        _source("codex/terra-short-0"),
    )
    grok = tuple(_source(f"codex/grok-only-{index}") for index in range(8))
    sources = terra + grok
    for index, source in enumerate(sources, start=1):
        _ = _install_pair(
            tmp_path,
            source,
            detail_repetitions=index * 30,
        )
    evidence = tuple(
        ReviewSourceEvidence(
            source_id=source.source_id,
            reviewers=("gpt-5.6-terra",),
            reviewer_report_count=1,
        )
        for source in terra
    ) + tuple(
        ReviewSourceEvidence(
            source_id=source.source_id,
            reviewers=("grok-4.5",),
            reviewer_report_count=1,
        )
        for source in grok
    )
    inventory = _build(
        tmp_path,
        sources,
        review_scan=_review_scan(evidence),
    )
    pilot = select_pilot(inventory)
    assert pilot.selected_count == 9
    assert pilot.reviewer_counts == {
        "gpt-5.6-terra": 3,
        "grok-4.5": 6,
    }
    assert pilot.product_counts == {
        "claude-code": 2,
        "codex": 7,
    }
    terra_products = {
        selection.product for selection in pilot.selections if selection.reviewer == "gpt-5.6-terra"
    }
    grok_products = {
        selection.product for selection in pilot.selections if selection.reviewer == "grok-4.5"
    }
    assert terra_products == {"claude-code", "codex"}
    assert grok_products == {"codex"}
    inventory_by_id = {item.source_id: item for item in inventory.items}
    assert all(
        inventory_by_id[selection.source_id].admission_reviewer == selection.reviewer
        for selection in pilot.selections
    )


def test_atomic_inventory_write_is_strict_idempotent_and_sanitized(
    tmp_path: Path,
) -> None:
    """An exact replay does not replace bytes and JSON contains no absolute path."""
    source = _source("codex/atomic")
    _ = _install_pair(tmp_path, source)
    inventory = _build(tmp_path, (source,))
    output = tmp_path / ".ai-local/audit-inventory.json"
    assert write_inventory_atomic(output, inventory)
    first = output.read_bytes()
    assert not write_inventory_atomic(output, inventory)
    assert output.read_bytes() == first
    restored = AuditInventory.model_validate_json(first)
    assert restored == inventory
    decoded = first.decode("utf-8")
    assert str(tmp_path) not in decoded
    assert not tuple(output.parent.glob(f".{output.name}.*.tmp"))


def test_inventory_contract_rejects_absolute_paths_and_duplicate_evidence(
    tmp_path: Path,
) -> None:
    """Strict models reject data that could hide ownership or local path details."""
    source = _source("codex/strict")
    _ = _install_pair(tmp_path, source)
    inventory = _build(tmp_path, (source,))
    document = inventory.model_dump(mode="json")
    document["manifest_path"] = "C:/private/audit-inventory.json"
    with pytest.raises(ValueError, match="sanitized repository-relative"):
        _ = AuditInventory.model_validate(document)
    evidence = ReviewSourceEvidence(
        source_id=source.source_id,
        reviewers=("gpt-5.6-terra",),
        reviewer_report_count=1,
    )
    with pytest.raises(ValueError, match="duplicate source evidence"):
        _ = ReviewScan(
            files_scanned=2,
            exact_source_reports=2,
            ignored_malformed=0,
            ignored_unknown_source=0,
            ignored_without_reviewer=0,
            evidence=(evidence, evidence),
        )


def test_full_manifest_conservation_has_303_known_statuses(
    tmp_path: Path,
) -> None:
    """The public builder classifies every canonical manifest source exactly once."""
    manifest = tmp_path / "source-ai/sources.yaml"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    _ = manifest.write_bytes((ROOT / "source-ai/sources.yaml").read_bytes())
    inventory = build_inventory(tmp_path)
    assert inventory.source_count == 303
    assert len(inventory.items) == 303
    assert len({item.source_id for item in inventory.items}) == 303
    assert inventory.unknown_source_count == 0
    assert sum(inventory.status_counts.values()) == 303
    assert inventory.status_counts[InventoryStatus.MISSING_SOURCE.value] == 303
