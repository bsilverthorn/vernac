import os

from datetime import datetime

from rich import print as rich_print
from rich.markup import escape
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)

from vernac.util import (
    str_to_filename,
    call_with_supported_args,
)
from vernac.stages.interface import (
    VernacStage,
    StageContext,
    StageAction,
)

progress = Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    TaskProgressColumn(),
)

def print(*args, **kwargs):
    def yield_args():
        for arg in args:
            if isinstance(arg, str):
                yield escape(arg)
            else:
                yield arg

    rich_print(*yield_args(), **kwargs)

def leaf_log_dir_name(stage_number: int, stage_title: str):
    return str_to_filename(f"{stage_number:02d}_{stage_title}")

class VernacPipeline:
    def __init__(
            self, name: str,
            stages: list[VernacStage],
            logs_base_path: str | None = None,
            verbose: bool = False,
        ):
        self.name = name
        self.stages = stages
        self.verbose = verbose

        if logs_base_path is None:
            timestamp_dir_name = datetime.now().strftime("%Y%m%d%H%M%S")

            self.logs_base_path = os.path.join("logs", timestamp_dir_name)
        else:
            self.logs_base_path = logs_base_path

    async def run(self, state: dict | None = None) -> dict:
        state = {} if state is None else state
        stage_index = 0
        stage_number = 0

        with progress:
            while stage_index < len(self.stages):
                stage = self.stages[stage_index]
                stage_dir_name = leaf_log_dir_name(stage_number, stage.title)
                log_dir = os.path.join(self.logs_base_path, self.name, stage_dir_name)

                if stage.title is None:
                    task = None
                else:
                    task = progress.add_task(stage.title, total=stage.steps)

                context = StageContext(
                    pipeline=self,
                    log_dir=log_dir,
                    verbose=self.verbose,
                    progress=progress,
                    progress_task=task,
                )
                called = call_with_supported_args(
                    stage.run,
                    dict(context=context) | state,
                )
                output = await called

                if task is not None:
                    progress.update(task, completed=stage.steps)

                match output.action:
                    case StageAction.LOOP:
                        stage_index = 0

                    case StageAction.NEXT:
                        stage_index += 1

                stage_number += 1
                state |= output.state

        return state
