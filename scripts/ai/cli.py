"""Typer entrypoint for AI handbook sync."""

# Copyright 2026

import importlib
from collections.abc import Callable
from types import ModuleType
from typing import Protocol, runtime_checkable

import typer

app = typer.Typer(help="AI handbook CLI entrypoint")


@runtime_checkable
class SyncCommand(Protocol):
    """Contract for the lazily loaded sync module."""

    main: Callable[[], int]


def _run_sync() -> int:
    """Dispatch to the lazily imported sync command and return its exit code."""
    try:
        command = _load_sync_module()
    except ModuleNotFoundError as exc:
        if exc.name != "scripts.ai.sync":
            raise
        raise typer.Exit(code=1) from exc

    if not isinstance(command, SyncCommand):
        message = "scripts.ai.sync main() contract is missing"
        raise TypeError(message)
    return command.main()


def _run_english_sync() -> int:
    """Dispatch to the complete English synchronization command."""
    command = importlib.import_module("scripts.ai.sync_english")
    if not isinstance(command, SyncCommand):
        message = "scripts.ai.sync_english main() contract is missing"
        raise TypeError(message)
    return command.main()


def _load_sync_module() -> ModuleType:
    return importlib.import_module("scripts.ai.sync")


@app.callback(invoke_without_command=True)
def root() -> None:
    """AI handbook CLI entrypoint."""


@app.command(name="sync", help="Synchronize official AI handbook docs")
def sync() -> None:
    """Synchronize AI handbook content."""
    raise typer.Exit(code=_run_sync())


@app.command(name="sync-english", help="Synchronize the complete English handbook")
def sync_english() -> None:
    """Synchronize all English sources without invoking a translator."""
    raise typer.Exit(code=_run_english_sync())


def main() -> None:
    """Run the Typer app."""
    command = typer.main.get_command(app)
    command(prog_name="scripts.ai.cli")


if __name__ == "__main__":
    raise SystemExit(main())
