import os
import os.path
import re
import argparse

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

from vernac.util import call_with_supported_args
from vernac.stages.interface import (
    StageContext,
    StageAction,
)
from vernac.stages.all import (
    ReadSourceStage,
    GenerateCodeStage,
    GuessDependenciesStage,
    PackageStage,
    CheckHelpStage,
    CheckTestsStage,
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
    title_lower = stage_title.lower()
    only_alpha = re.sub(r"[^\w\s]", "", title_lower)
    spaces_replaced = re.sub(r"\s+", "_", only_alpha)
    leaf_dir = f"{stage_number:02d}_{spaces_replaced}"

    return leaf_dir

def main(in_path: str, out_path: str, verbose: bool = False):
    stages = [
        ReadSourceStage("Reading source"),
        GenerateCodeStage("Generating code"),
        GuessDependenciesStage("Guessing dependencies"),
        PackageStage("Packaging", out_path=out_path),
        CheckHelpStage("Checking --help"),
        CheckTestsStage("Checking test output"),
    ]
    stage_index = 0
    stage_number = 0
    state = dict(in_path=in_path)
    middle_dir_name = datetime.now().strftime("%Y%m%d%H%M%S")

    with progress:
        while stage_index < len(stages):
            stage = stages[stage_index]
            leaf_dir_name = leaf_log_dir_name(stage_number, stage.title)
            log_dir = os.path.join("logs", middle_dir_name, leaf_dir_name)

            os.makedirs(log_dir)

            task = progress.add_task(stage.title, total=stage.steps)

            context = StageContext(
                log_dir=log_dir,
                progress=progress,
                progress_task=task,
            )
            output = call_with_supported_args(
                stage.run,
                dict(context=context) | state,
            )

            progress.update(task, completed=stage.steps)

            match output.action:
                case StageAction.LOOP:
                    stage_index = 0

                case StageAction.NEXT:
                    stage_index += 1

            stage_number += 1
            state |= output.state

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        dest="in_path",
        type=str,
        metavar="PATH",
    )
    parser.add_argument(
        "-o",
        dest="out_path",
        type=str,
        metavar="PATH",
        required=True,
    )
    parser.add_argument(
        "-v",
        dest="verbose",
        action="store_true",
    )

    args = parser.parse_args()

    return args

def script_main():
    main(**vars(parse_args()))

if __name__ == "__main__":
    script_main()
