import os.path
import json

from typing import Callable
from enum import (
    Enum,
    auto,
)
from dataclasses import dataclass

from rich.progress import (
    Progress,
    TaskID,
)

class VernacStage:
    title: str
    steps: int

class StageContext:
    log_dir: str

    def __init__(
            self,
            log_dir: str,
            progress: Progress,
            progress_task: TaskID,
        ):
        self.log_dir = log_dir
        self._progress = progress
        self._progress_task = progress_task

    def get_log_path(self, rel_path: str) -> str:
        return os.path.join(self.log_dir, rel_path)

    def log_bytes(self, rel_path: str, contents: bytes):
        with open(self.get_log_path(rel_path), "wb") as log_file:
            log_file.write(contents)

    def log_text(self, rel_path: str, contents: str):
        self.log_bytes(rel_path, contents.encode("utf-8"))

    def log_json(self, rel_path: str, contents: any, indent=2, **kwargs):
        self.log_text(rel_path, json.dumps(contents, indent=indent, **kwargs))

    def advance_progress(self, advance: float = 1):
        self._progress.update(self._progress_task, advance=advance)

    def update_progress(self, completed: float):
        self._progress.update(self._progress_task, completed=completed)

class StageAction(Enum):
    NEXT = auto()
    LOOP = auto()

@dataclass
class StageOutput:
    action: StageAction
    state: dict
