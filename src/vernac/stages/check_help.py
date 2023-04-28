import os.path
import subprocess

from subprocess import (
    check_output,
    CalledProcessError,
)

from vernac.stages.interface import (
    VernacStage,
    StageContext,
    StageAction,
    StageOutput,
)
from vernac.stages.generate_code import TestFailure

class CheckHelpStage(VernacStage):
    steps = 1

    def __init__(self, title: str):
        self.title = title

    def run(
            self,
            context: StageContext,
            python: str,
            out_path: str,
            **kwargs,
        ) -> StageOutput:
        try:
            output = check_output(
                [
                    os.path.abspath(out_path),
                    "--help",
                ],
                stderr=subprocess.STDOUT,
                timeout=8.0,
            )
        except CalledProcessError as error:
            context.log_bytes("output.txt", error.output)

            failure = TestFailure(
                input="Ran program with `--help`.",
                expected="Standard help text",
                actual=error.output,
            )

            return StageOutput(
                action=StageAction.LOOP,
                state=dict(test_failures=[failure], first_draft=python),
            )
        else:
            context.log_bytes("output.txt", output)

            return StageOutput(
                action=StageAction.NEXT,
                state=dict(test_failures=[]),
            )

