import sys

from vernac.openai import complete_chat
from vernac.util import normalize_progress
from vernac.stages.interface import (
    VernacStage,
    StageContext,
    StageAction,
    StageOutput,
)

class GuessDependenciesStage(VernacStage):
    steps = 100

    def __init__(self, title: str):
        self.title = title

    def run(
            self,
            context: StageContext,
            python: str,
            **kwargs,
        ) -> StageOutput:
        system_prompt = (
            "You are an expert programmer working on contract. "
            "The user, your client, will share a Python program. "
            "Respond with a list of Python packages that must be installed to run the program. "
            "Standard library packages do not need to be installed and should be ignored. "
            "Write one package per line. "
            "If no packages are required, write nothing. "
            "Do not write any other formatting or commentary."
        )
        user_prompt = (
            "Please write a list of Python packages required to run the following program. "
            f"\n\n# Source Code\n\n{python}\n"
        )
        chat_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        context.log_json("prompt.json", chat_messages)

        def on_token(i: int):
            context.update_progress(completed=normalize_progress(i))

        chat_completion = complete_chat(
            chat_messages,
            model="gpt-4",
            on_token=on_token,
        )

        context.log_text("completion.txt", chat_completion)

        dependencies = set(chat_completion.splitlines()) - sys.stdlib_module_names
        dependencies = [d for d in dependencies if not d.startswith("vnprog")]

        context.log_json("dependencies.json", dependencies)

        return StageOutput(
            action=StageAction.NEXT,
            state=dict(python=python, dependencies=dependencies),
        )
