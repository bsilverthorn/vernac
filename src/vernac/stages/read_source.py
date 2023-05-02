import os.path

from vernac.stages.interface import (
    VernacStage,
    StageContext,
    StageAction,
    StageOutput,
)

class ReadSourceStage(VernacStage):
    steps = 1

    def __init__(self, title: str):
        self.title = title

    def read_source(self, context: StageContext, in_path: str) -> tuple[str, str]:
        in_name = os.path.basename(in_path)

        with open(in_path, "r") as src_file:
            src = src_file.read()

        context.log_text(os.path.join("sources", in_name), src)

        return (in_name, src)

    def run(self, context: StageContext, in_paths: list[str]) -> StageOutput:
        english_all = dict(self.read_source(context, p) for p in in_paths)

        return StageOutput(
            action=StageAction.NEXT,
            state=dict(english_all=english_all),
        )
