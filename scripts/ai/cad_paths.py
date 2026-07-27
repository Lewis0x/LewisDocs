# Copyright 2026

"""CAD Markdown path selection."""

from pathlib import Path


def iter_cad_markdown(docs_root: Path) -> tuple[Path, ...]:
    """Return CAD Markdown paths below the documentation root."""
    return tuple(
        sorted(
            path
            for path in docs_root.rglob("*.md")
            if path.is_file()
            and not path.is_symlink()
            and path.relative_to(docs_root).parts[0] != "ai"
        )
    )
