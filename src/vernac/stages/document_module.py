from vernac.openai import complete_chat
from vernac.util import (
    normalize_progress,
    replace_ext,
)
from vernac.stages.interface import (
    VernacStage,
    StageContext,
    StageAction,
    StageOutput,
)

SYSTEM_PROMPT = """
You are an expert programmer working on contract. The user, your client, will provide the description and source code of an existing module. Respond with clear documentation of the module interface. Your documentation should be structed as two Markdown sections, as follows:

## Module interface

<specific method signatures, classes, and other details necessary to use the module. be concise.>

## Module notes

<key concepts for using the module effectively. copy any important text from the description. do not duplicate information provided in the interface section above.>
"""

USER_PROMPT_TEMPLATE = """
Filename: `{py_name}`

{description}

# Module source
        
{source}
"""

class DocumentModuleStage(VernacStage):
    steps = 100

    def __init__(self, title: str):
        self.title = title

    def run(
            self,
            context: StageContext,
            english: str,
            python: str,
            vn_name: str,
        ) -> StageOutput:
        py_name = replace_ext(vn_name, "py").replace("-", "_")

        user_prompt = USER_PROMPT_TEMPLATE.format(
            py_name=py_name,
            description=english,
            source=python,
        )

        chat_messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
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

        return StageAction.NEXT.out(
            py_name=py_name,
            documentation=chat_completion,
        )
