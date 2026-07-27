# Copyright 2026

"""Public AI build inventory verification."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, NoReturn

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError

from scripts.ai.errors import AIAgentError, ErrorCode
from scripts.ai.manifest import load_sources

if TYPE_CHECKING:
    from scripts.ai.types import SourceManifest


@dataclass(frozen=True, slots=True)
class VerifyBuildOptions:
    """Paths required to verify one public VitePress build."""

    repo_root: Path
    dist_root: Path
    manifest_path: Path


class _SearchFields(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="ignore", strict=True)

    title: str = ""
    titles: tuple[str, ...] = ()


class _SearchIndex(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="ignore", strict=True)

    document_ids: dict[str, str] = Field(validation_alias="documentIds")
    stored_fields: dict[str, _SearchFields] = Field(validation_alias="storedFields")


def verify_dist(options: VerifyBuildOptions) -> None:
    """Verify the public HTML and local-search route inventory."""
    try:
        manifest = load_sources(options.manifest_path)
        expected = _expected_routes(manifest)
        html_routes = frozenset(
            f"/{path.relative_to(options.dist_root).with_suffix('').as_posix()}"
            for path in (options.dist_root / "ai").rglob("*.html")
            if path.is_file() and not path.is_symlink()
        )
        if html_routes != expected:
            _validation_failed()
        search = _load_search_index(options.dist_root)
        ai_routes = frozenset(
            route.split("#", maxsplit=1)[0]
            for route in search.document_ids.values()
            if route == "/ai" or route.startswith("/ai/")
        )
        if ai_routes != expected:
            _validation_failed()
        titles = tuple(field.title for field in search.stored_fields.values() if field.title)
        if not any(title.startswith("EN · ") for title in titles):
            _validation_failed()
        if not any(title.startswith("中文 · ") for title in titles):
            _validation_failed()
    except AIAgentError:
        raise
    except (OSError, UnicodeDecodeError, ValidationError, ValueError):
        _validation_failed()


def main() -> int:
    """Verify the repository's current public build."""
    repo_root = Path(__file__).resolve().parents[2]
    try:
        verify_dist(
            VerifyBuildOptions(
                repo_root=repo_root,
                dist_root=repo_root / "docs" / ".vitepress" / "dist",
                manifest_path=repo_root / "source-ai" / "sources.yaml",
            )
        )
    except AIAgentError as error:
        _ = sys.stderr.write(f"{error.code}: public AI build verification failed\n")
        return 1
    _ = sys.stdout.write("verified 22 AI handbook routes\n")
    return 0


def _expected_routes(manifest: SourceManifest) -> frozenset[str]:
    return frozenset(
        (
            *(
                f"/ai/{lang}/{source.product}/{source.slug}"
                for source in manifest.root
                for lang in ("en", "zh-CN")
            ),
            "/ai/zh-CN/learn/claude-code",
            "/ai/zh-CN/learn/codex",
        )
    )


def _load_search_index(dist_root: Path) -> _SearchIndex:
    chunks = tuple(sorted((dist_root / "assets" / "chunks").glob("@localSearchIndex*.js")))
    if len(chunks) != 1:
        _validation_failed()
    text = chunks[0].read_text(encoding="utf-8")
    start = text.find("`")
    end = text.rfind("`;")
    if start < 0 or end <= start:
        _validation_failed()
    raw_template = text[start + 1 : end]
    quoted_template = '"' + raw_template.replace('"', '\\"') + '"'
    cooked_json = TypeAdapter(str).validate_json(quoted_template)
    return _SearchIndex.model_validate_json(cooked_json)


def _validation_failed() -> NoReturn:
    raise AIAgentError(
        code=ErrorCode.VALIDATION_FAILED,
        message="public AI build inventory is invalid",
    )


if __name__ == "__main__":
    raise SystemExit(main())
