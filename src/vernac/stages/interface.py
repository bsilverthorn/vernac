import os
import os.path
import json

from typing import (
    Any,
    TYPE_CHECKING,
)
from enum import (
    Enum,
    auto,
)
from dataclasses import dataclass

from rich.progress import (
    Progress,
    TaskID,
)

if TYPE_CHECKING:
    from vernac.pipeline import VernacPipeline

class VernacStage:
    title: str | None = None
    steps: int | None = None

class StageContext:
    log_dir: str

    def __init__(
            self,
            pipeline: "VernacPipeline",
            log_dir: str,
            verbose: bool,
            progress: Progress,
            progress_task: TaskID,
        ):
        self.pipeline = pipeline
        self.log_dir = log_dir
        self.verbose = verbose
        self._progress = progress
        self._progress_task = progress_task

    def get_log_path(self, rel_path: str) -> str:
        log_path = os.path.join(self.log_dir, rel_path)
        (log_dir, _) = os.path.split(log_path)

        os.makedirs(log_dir, exist_ok=True)

        return log_path

    def log_bytes(self, rel_path: str, contents: bytes):
        with open(self.get_log_path(rel_path), "wb") as log_file:
            log_file.write(contents)

    def log_text(self, rel_path: str, contents: str):
        self.log_bytes(rel_path, contents.encode("utf-8"))

    def log_json(self, rel_path: str, contents: Any, indent=2, **kwargs):
        self.log_text(rel_path, json.dumps(contents, indent=indent, **kwargs))

    def advance_progress(self, advance: float = 1):
        self._progress.update(self._progress_task, advance=advance)

    def update_progress(self, completed: float):
        self._progress.update(self._progress_task, completed=completed)

class StageAction(Enum):
    NEXT = auto()
    LOOP = auto()

    @classmethod
    def out(cls, **state: Any) -> "StageOutput":
        return StageOutput(
            action=cls.NEXT,
            state=state,
        )

@dataclass
class StageOutput:
    action: StageAction
    state: dict

