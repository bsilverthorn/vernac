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

    def run(self, context: StageContext, in_path: str) -> StageOutput:
        with open(in_path, "r") as src_file:
            src = src_file.read()

        context.log_text("source.vn", src)

        return StageOutput(
            action=StageAction.NEXT,
            state=dict(english=src),
        )
