# Copyright 2026

"""Strict bilingual learning-path data boundary."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, Literal, NoReturn, Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from scripts.ai.errors import AIAgentError, ErrorCode

if TYPE_CHECKING:
    from pathlib import Path

    from scripts.ai.types import SourceManifest

TaskKind = Literal["practice", "verify"]
LearningLanguage = Literal["en", "zh-CN"]
Product = Literal["claude-code", "codex"]

_SAFE_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class LearningTask(BaseModel):
    """One language-neutral task."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True,
        extra="forbid",
        str_strip_whitespace=True,
    )

    id: str
    kind: TaskKind

    @field_validator("id")
    @classmethod
    def _validate_id(cls, value: str) -> str:
        if _SAFE_ID_RE.fullmatch(value) is None:
            msg = "learning task id must use lowercase kebab-case"
            raise ValueError(msg)
        return value


class LearningStage(BaseModel):
    """One ordered stage in a learning path."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True,
        extra="forbid",
        str_strip_whitespace=True,
    )

    id: str
    source_ids: tuple[str, ...]
    tasks: tuple[LearningTask, ...]

    @field_validator("id")
    @classmethod
    def _validate_id(cls, value: str) -> str:
        if _SAFE_ID_RE.fullmatch(value) is None:
            msg = "learning stage id must use lowercase kebab-case"
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def _validate_contents(self) -> Self:
        if not self.source_ids:
            msg = "learning stage must reference at least one source"
            raise ValueError(msg)
        if len(set(self.source_ids)) != len(self.source_ids):
            msg = "learning stage contains duplicate source ids"
            raise ValueError(msg)
        if not self.tasks:
            msg = "learning stage must contain at least one task"
            raise ValueError(msg)
        task_ids = [task.id for task in self.tasks]
        if len(set(task_ids)) != len(task_ids):
            msg = "learning stage contains duplicate task ids"
            raise ValueError(msg)
        return self


class LearningPath(BaseModel):
    """Canonical language-neutral learning-path structure."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True,
        extra="forbid",
        str_strip_whitespace=True,
    )

    version: Literal[1]
    product: Product
    stages: tuple[LearningStage, ...]

    @model_validator(mode="after")
    def _validate_unique_ids(self) -> Self:
        if not self.stages:
            msg = "learning path must contain at least one stage"
            raise ValueError(msg)
        stage_ids = [stage.id for stage in self.stages]
        if len(set(stage_ids)) != len(stage_ids):
            msg = "learning path contains duplicate stage ids"
            raise ValueError(msg)
        task_ids = [task.id for stage in self.stages for task in stage.tasks]
        if len(set(task_ids)) != len(task_ids):
            msg = "learning task ids must be globally unique within a product"
            raise ValueError(msg)
        return self


class LearningStageCopy(BaseModel):
    """Localized copy for one canonical stage."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True,
        extra="forbid",
        str_strip_whitespace=True,
    )

    title: str
    objective: str
    risk: str

    @field_validator("title", "objective", "risk")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        if not value:
            msg = "learning stage copy must be non-empty"
            raise ValueError(msg)
        return value


class LearningTaskCopy(BaseModel):
    """Localized copy for one canonical task."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True,
        extra="forbid",
        str_strip_whitespace=True,
    )

    title: str
    instruction: str
    done_when: str

    @field_validator("title", "instruction", "done_when")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        if not value:
            msg = "learning task copy must be non-empty"
            raise ValueError(msg)
        return value


class LearningCopy(BaseModel):
    """Localized display copy that cannot alter canonical ordering or behavior."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True,
        extra="forbid",
        str_strip_whitespace=True,
    )

    version: Literal[1]
    product: Product
    title: str
    summary: str
    stages: dict[str, LearningStageCopy]
    tasks: dict[str, LearningTaskCopy]

    @field_validator("title", "summary")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        if not value:
            msg = "learning page copy must be non-empty"
            raise ValueError(msg)
        return value


@dataclass(frozen=True, slots=True)
class LearningBundle:
    """Validated structure and its two isomorphic language files."""

    path: LearningPath
    en: LearningCopy
    zh_cn: LearningCopy


def load_learning_bundles(
    learning_root: Path,
    manifest: SourceManifest,
) -> tuple[LearningBundle, ...]:
    """Load exactly two complete bilingual learning paths."""
    try:
        if learning_root.is_symlink() or not learning_root.is_dir():
            _fail()
        expected = {
            f"{product}.{suffix}.json"
            for product in ("claude-code", "codex")
            for suffix in ("path", "en", "zh-CN")
        }
        if {path.name for path in learning_root.iterdir()} != expected:
            _fail()
        bundles = tuple(
            _load_bundle(learning_root, product, manifest)
            for product in ("claude-code", "codex")
        )
    except AIAgentError:
        raise
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        _fail(cause=exc)
    return bundles


def _load_bundle(
    root: Path,
    product: Product,
    manifest: SourceManifest,
) -> LearningBundle:
    path = LearningPath.model_validate(_read_json(root / f"{product}.path.json"))
    en = LearningCopy.model_validate(_read_json(root / f"{product}.en.json"))
    zh_cn = LearningCopy.model_validate(_read_json(root / f"{product}.zh-CN.json"))
    if path.product != product or en.product != product or zh_cn.product != product:
        _fail()

    valid_sources = {source.id: source.product for source in manifest.root}
    for stage in path.stages:
        for source_id in stage.source_ids:
            if valid_sources.get(source_id) != product:
                _fail(source_id)

    expected_stages = {stage.id for stage in path.stages}
    expected_tasks = {
        task.id
        for stage in path.stages
        for task in stage.tasks
    }
    for copy in (en, zh_cn):
        if set(copy.stages) != expected_stages or set(copy.tasks) != expected_tasks:
            _fail()
    return LearningBundle(path=path, en=en, zh_cn=zh_cn)


def _read_json(path: Path) -> object:
    if path.is_symlink() or not path.is_file():
        _fail()
    return json.loads(path.read_text(encoding="utf-8"))


def _fail(
    source_id: str | None = None,
    cause: Exception | None = None,
) -> NoReturn:
    raise AIAgentError(
        code=ErrorCode.VALIDATION_FAILED,
        message="learning path validation failed",
        source_id=source_id,
    ) from cause
