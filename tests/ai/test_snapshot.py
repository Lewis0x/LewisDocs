# Copyright 2026
# ruff: noqa: INP001
"""Behavior tests for filesystem snapshots and injectable operations."""

from __future__ import annotations

import os
from dataclasses import dataclass
from hashlib import sha256
from typing import TYPE_CHECKING, Final, Literal

import pytest

from scripts.ai.errors import AIAgentError, ErrorCode
from scripts.ai.snapshot import FileDigest, RealFileOps, Snapshot, tree_snapshot

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

OperationName = Literal["copy_tree", "replace", "write_bytes", "remove"]
FAULT_LABELS: Final[tuple[str, ...]] = (
    "candidate:en",
    "candidate:zh-CN",
    "next:en",
    "next:zh-CN",
    "rename:en-live-to-backup",
    "rename:zh-CN-live-to-backup",
    "rename:en-next-to-live",
    "rename:zh-CN-next-to-live",
    "report:temp-write",
    "report:replace",
    "cleanup",
)


@dataclass(frozen=True, slots=True)
class _RecordedOperation:
    name: OperationName
    fault: str | None


@dataclass(frozen=True, slots=True)
class _FaultOperation:
    name: OperationName
    fault: str
    source: Path
    destination: Path


class _FakeFileOps:
    _fail_once_at: str
    _has_failed: bool
    _real: RealFileOps
    operations: list[_RecordedOperation]

    def __init__(self, fail_once_at: str) -> None:
        self._fail_once_at = fail_once_at
        self._has_failed = False
        self._real = RealFileOps()
        self.operations = []

    def copy_tree(self, source: Path, destination: Path, fault: str | None) -> None:
        self._run(
            _RecordedOperation(name="copy_tree", fault=fault),
            lambda: self._real.copy_tree(source, destination, fault=None),
        )

    def replace(self, source: Path, destination: Path, fault: str | None) -> None:
        self._run(
            _RecordedOperation(name="replace", fault=fault),
            lambda: self._real.replace(source, destination, fault=None),
        )

    def write_bytes(self, path: Path, data: bytes, fault: str | None) -> None:
        self._run(
            _RecordedOperation(name="write_bytes", fault=fault),
            lambda: self._real.write_bytes(path, data, fault=None),
        )

    def remove(self, path: Path, fault: str | None) -> None:
        self._run(
            _RecordedOperation(name="remove", fault=fault),
            lambda: self._real.remove(path, fault=None),
        )

    def _run(self, operation: _RecordedOperation, execute: Callable[[], None]) -> None:
        self.operations.append(operation)
        if operation.fault == self._fail_once_at and not self._has_failed:
            self._has_failed = True
            raise AIAgentError(code=ErrorCode.WRITE_FAILED, message="injected write failure")
        execute()


def test_tree_snapshot_is_sorted_posix_relative_and_hashes_bytes(tmp_path: Path) -> None:
    """Given nested files, return their sorted POSIX paths and SHA-256 byte digests."""
    root = tmp_path / "content"
    nested = root / "nested"
    nested.mkdir(parents=True)
    first = root / "zeta.txt"
    second = nested / "alpha.md"
    _ = first.write_bytes(b"zeta")
    _ = second.write_bytes(b"alpha")

    snapshot = tree_snapshot(root)

    assert snapshot == Snapshot(  # noqa: S101
        files=(
            FileDigest(
                path="nested/alpha.md",
                sha256=sha256(b"alpha").hexdigest(),
            ),
            FileDigest(path="zeta.txt", sha256=sha256(b"zeta").hexdigest()),
        )
    )


def test_tree_snapshot_handles_empty_trees_and_changes_when_bytes_change(tmp_path: Path) -> None:
    """Return an empty snapshot and a changed digest after bytes change."""
    root = tmp_path / "content"
    root.mkdir()

    empty = tree_snapshot(root)
    target = root / "page.md"
    _ = target.write_bytes(b"before")
    before = tree_snapshot(root)
    _ = target.write_bytes(b"after")
    after = tree_snapshot(root)

    assert empty == Snapshot(files=())  # noqa: S101
    assert before != after  # noqa: S101
    assert before.files[0].path == "page.md"  # noqa: S101
    assert before.files[0].sha256 == sha256(b"before").hexdigest()  # noqa: S101
    assert after.files[0].sha256 == sha256(b"after").hexdigest()  # noqa: S101


@pytest.mark.parametrize("entry_kind", ["symlink", "fifo"])
def test_tree_snapshot_rejects_non_regular_entries_without_content_leakage(
    tmp_path: Path,
    entry_kind: str,
) -> None:
    """Reject symlink and FIFO entries without including their content in the error."""
    root = tmp_path / "content"
    root.mkdir()
    target = root / "secret-content.txt"
    _ = target.write_bytes(b"do not leak")
    unsafe = root / "unsafe"

    match entry_kind:
        case "symlink":
            unsafe.symlink_to(target)
        case "fifo":
            os.mkfifo(unsafe)
        case unreachable:
            pytest.fail(f"unexpected entry kind {unreachable}")

    with pytest.raises(AIAgentError) as exc_info:
        _ = tree_snapshot(root)

    assert exc_info.value.code == ErrorCode.VALIDATION_FAILED  # noqa: S101
    assert "do not leak" not in str(exc_info.value)  # noqa: S101


def _fault_operation(root: Path, fault: str) -> _FaultOperation:
    match fault:
        case "candidate:en" | "candidate:zh-CN" | "next:en" | "next:zh-CN":
            source = root / "source"
            _ = (source / "page.md").parent.mkdir(parents=True)
            _ = (source / "page.md").write_bytes(b"copied")
            return _FaultOperation("copy_tree", fault, source, root / "destination")
        case (
            "rename:en-live-to-backup"
            | "rename:zh-CN-live-to-backup"
            | "rename:en-next-to-live"
            | "rename:zh-CN-next-to-live"
            | "report:replace"
        ):
            source = root / "source"
            destination = root / "destination"
            _ = source.write_bytes(b"new")
            _ = destination.write_bytes(b"old")
            return _FaultOperation("replace", fault, source, destination)
        case "report:temp-write":
            destination = root / "nested" / "report.json"
            return _FaultOperation("write_bytes", fault, destination, destination)
        case "cleanup":
            source = root / "cleanup"
            _ = source.write_bytes(b"remove")
            return _FaultOperation("remove", fault, source, source)
        case unreachable:
            pytest.fail(f"unexpected fault label {unreachable}")


def _run_fault_operation(fake: _FakeFileOps, operation: _FaultOperation) -> None:
    match operation.name:
        case "copy_tree":
            fake.copy_tree(operation.source, operation.destination, operation.fault)
        case "replace":
            fake.replace(operation.source, operation.destination, operation.fault)
        case "write_bytes":
            fake.write_bytes(operation.destination, b"written", operation.fault)
        case "remove":
            fake.remove(operation.source, operation.fault)


def _assert_fault_operation_not_applied(operation: _FaultOperation) -> None:
    match operation.name:
        case "copy_tree" | "write_bytes":
            assert not operation.destination.exists()  # noqa: S101
        case "replace":
            assert operation.source.read_bytes() == b"new"  # noqa: S101
            assert operation.destination.read_bytes() == b"old"  # noqa: S101
        case "remove":
            assert operation.source.read_bytes() == b"remove"  # noqa: S101


def _assert_fault_operation_applied(operation: _FaultOperation) -> None:
    match operation.name:
        case "copy_tree":
            assert (operation.destination / "page.md").read_bytes() == b"copied"  # noqa: S101
        case "replace":
            assert not operation.source.exists()  # noqa: S101
            assert operation.destination.read_bytes() == b"new"  # noqa: S101
        case "write_bytes":
            assert operation.destination.read_bytes() == b"written"  # noqa: S101
        case "remove":
            assert not operation.source.exists()  # noqa: S101


@pytest.mark.parametrize("fault", FAULT_LABELS)
def test_fake_file_ops_fails_once_before_each_fault_label_and_logs_transparently(
    tmp_path: Path,
    fault: str,
) -> None:
    """Fail each caller-provided label before its operation, then execute once."""
    fake = _FakeFileOps(fail_once_at=fault)
    operation = _fault_operation(tmp_path, fault)
    expected = _RecordedOperation(name=operation.name, fault=fault)

    with pytest.raises(AIAgentError) as exc_info:
        _run_fault_operation(fake, operation)

    assert exc_info.value.code == ErrorCode.WRITE_FAILED  # noqa: S101
    assert fake.operations == [expected]  # noqa: S101
    _assert_fault_operation_not_applied(operation)

    _run_fault_operation(fake, operation)

    assert fake.operations == [expected, expected]  # noqa: S101
    _assert_fault_operation_applied(operation)


def test_real_file_ops_copies_a_tree_without_overwriting_a_destination(tmp_path: Path) -> None:
    """Copy the full tree into a newly created destination."""
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    _ = (source / "nested").mkdir(parents=True)
    _ = (source / "nested" / "page.md").write_bytes(b"copied")
    operations = RealFileOps()

    operations.copy_tree(source, destination, fault=None)

    assert (destination / "nested" / "page.md").read_bytes() == b"copied"  # noqa: S101


def test_real_file_ops_rejects_an_existing_copy_destination(tmp_path: Path) -> None:
    """Map a pre-existing copy destination to the safe write failure code."""
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    destination.mkdir()

    with pytest.raises(AIAgentError) as exc_info:
        RealFileOps().copy_tree(source, destination, fault=None)

    assert exc_info.value.code == ErrorCode.WRITE_FAILED  # noqa: S101


def test_real_file_ops_replaces_a_path_with_os_replace_semantics(tmp_path: Path) -> None:
    """Move source bytes into destination and remove the source path."""
    source = tmp_path / "next"
    destination = tmp_path / "live"
    _ = source.write_bytes(b"new")
    _ = destination.write_bytes(b"old")

    RealFileOps().replace(source, destination, fault=None)

    assert not source.exists()  # noqa: S101
    assert destination.read_bytes() == b"new"  # noqa: S101


def test_real_file_ops_writes_exact_bytes_after_creating_parents(tmp_path: Path) -> None:
    """Create the parent tree and preserve every byte."""
    target = tmp_path / "nested" / "output.bin"

    RealFileOps().write_bytes(target, b"\x00exact\xff", fault=None)

    assert target.read_bytes() == b"\x00exact\xff"  # noqa: S101


def test_real_file_ops_removes_exact_files_trees_and_links(tmp_path: Path) -> None:
    """Remove exact file, tree, and symlink targets without expanding scope."""
    file_path = tmp_path / "file"
    tree_path = tmp_path / "tree"
    link_path = tmp_path / "link"
    _ = file_path.write_bytes(b"file")
    _ = (tree_path / "nested").mkdir(parents=True)
    _ = (tree_path / "nested" / "file").write_bytes(b"tree")
    link_path.symlink_to(file_path)
    operations = RealFileOps()

    operations.remove(file_path, fault=None)
    operations.remove(tree_path, fault=None)
    operations.remove(link_path, fault=None)

    assert not file_path.exists()  # noqa: S101
    assert not tree_path.exists()  # noqa: S101
    assert not link_path.is_symlink()  # noqa: S101
