from enum import (
    Enum,
    auto,
)

from vernac.util import (
    str_to_filename,
    normalize_progress,
)
from vernac.openai import complete_chat
from vernac.stages.interface import (
    VernacStage,
    StageContext,
    StageAction,
    StageOutput,
)

class SourceType(Enum):
    MAIN = auto()
    MODULE = auto()

def classify_source_type(
        context: StageContext,
        filename: str,
        english: str,
    ) -> SourceType:
    # prepare prompt
    system_prompt = """
You are an expert programmer working on contract. The user, your client, has created specs for various modules. You need to start by identifying which spec describes the main module for the program.

The user will provide the spec. Please respond with MAIN if the spec appears to describe the main module. Otherwise respond with MODULE.

Only write MAIN or MODULE. Do not write any other text.
"""
    user_prompt = (
        f"Filename: {filename}\n\n"
        f"{english}"
    )
    chat_messages = [
        {"role": "system", "content": system_prompt.strip()},
        {"role": "user", "content": user_prompt.strip()},
    ]
    simple_filename = str_to_filename(filename)

    context.log_json(f"prompt_{simple_filename}.json", chat_messages)

    # run the prompt and extract tests
    def on_token(i: int):
        context.update_progress(completed=normalize_progress(i))

    chat_completion = complete_chat(
        chat_messages,
        model="gpt-3.5-turbo",
        on_token=on_token,
    )

    context.log_text(f"completion_{simple_filename}.txt", chat_completion)

    return SourceType[chat_completion.strip().upper()]

class MapModulesStage(VernacStage):
    steps = 1

    def __init__(self, title: str):
        self.title = title

    def run(self, context: StageContext, english_all: dict[str, str]) -> StageOutput:
        if len(english_all) == 1:
            english_types = {fn: SourceType.MAIN for fn in english_all}
        else:
            english_types = {
                fn: classify_source_type(context, fn, e)
                for fn, e in english_all.items()
            }

        (main,) = [fn for fn, t in english_types.items() if t == SourceType.MAIN]
        modules = [fn for fn, t in english_types.items() if t == SourceType.MODULE]

        return StageAction.NEXT.out(
            main_name=main,
            module_names=modules,
        )
