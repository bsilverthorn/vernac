from dataclasses import dataclass

from vernac.openai import complete_chat
from vernac.util import (
    normalize_progress,
    strip_markdown_fence,
)
from vernac.stages.interface import (
    VernacStage,
    StageContext,
    StageAction,
    StageOutput,
)
from vernac.stages.map_modules import SourceType

@dataclass
class TestFailure:
    input: str
    expected: str
    actual: str

def get_main_prompts(english: str) -> tuple[str, str]:
    system_prompt = (
        "You are an expert programmer working on contract. "
        "The user, your client, will provide a description of program functionality. "
        "Respond with Python 3 source code implementing that description.\n\n" 
        "Write one comment listing any dependencies to be `pip install`ed: `# DEPENDENCIES: ...`.\n\n"
        "Respond only with the source code inside a Markdown code block. "
        "Do not add commentary."
    )
    user_prompt = (
        "Please write the following program in Python 3. "
        "Include a `main` function that takes no arguments and returns nothing. "
        "Use `argparse` to parse command line arguments."
        f"\n\n# Program Spec\n\n{english}\n"
    )

    return (system_prompt, user_prompt)

def get_module_prompts(english: str) -> tuple[str, str]:
    system_prompt = (
        "You are an expert programmer working on contract. "
        "The user, your client, will provide a description of one specific module. "
        "Respond with Python 3 source code implementing that module.\n\n"
        "Write one comment listing any dependencies to be `pip install`ed: `# DEPENDENCIES: ...`.\n\n"
        "Respond only with the source code inside a Markdown code block. "
        "Do not add commentary."
    )
    user_prompt = english

    return (system_prompt, user_prompt)

class GenerateCodeStage(VernacStage):
    steps = 100

    def __init__(
            self,
            title: str,
            source_type: SourceType,
            inject_first: str | None = None,
            verbose: bool = False,
        ):
        self.title = title
        self.source_type = source_type
        self.inject_first = inject_first
        self.verbose = verbose

    def run(
            self,
            context: StageContext,
            english: str,
            modules: dict[str, dict] = {},
            first_draft: str | None = None,
            test_failures: list[TestFailure] = [],
        ) -> StageOutput:
        # skip codegen if we're injecting
        if self.inject_first is not None:
            output = StageOutput(
                action=StageAction.NEXT,
                state=dict(python=self.inject_first),
            )

            self.inject_first = None

            return output

        # prepare prompt
        match self.source_type:
            case SourceType.MAIN:
                (system_prompt, user_prompt) = get_main_prompts(english)

            case SourceType.MODULE:
                (system_prompt, user_prompt) = get_module_prompts(english)

        for (name, module) in modules.items():
            user_prompt += (
                f"\n\n# Module: `{module['py_name']}`\n\n"
                "This module has already been written. It can be imported from the `vnprog` package.\n\n"
                f"{module['documentation']}\n\n"
            )

        if first_draft is not None:
            user_prompt += (
                "# First draft\n\n"
                f"```\n{first_draft}```\n"
            )

        for (i, failure) in enumerate(test_failures):
            user_prompt += (
                f"\n# First draft test {i + 1}\n\n"
                f"Input: {failure.input}\n\n"
                f"Expected Output: {failure.expected}\n\n"
                f"Actual Output: {str(failure.actual)}\n"
            )

        chat_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        context.log_json("prompt.json", chat_messages)

        # run the prompt and make some code
        def on_token(i: int):
            context.update_progress(completed=normalize_progress(i))

        chat_completion = complete_chat(
            chat_messages,
            model="gpt-4",
            on_token=on_token,
        )

        context.log_text("completion.txt", chat_completion)

        python = strip_markdown_fence(chat_completion)

        if self.verbose:
            print(python)

        context.log_text("code.py", python)

        return StageOutput(
            action=StageAction.NEXT,
            state=dict(python=python),
        )
