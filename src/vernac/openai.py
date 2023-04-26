import os

from typing import (
    cast,
    Callable,
    Iterable,
)

import openai

from openai import ChatCompletion

openai.api_key = os.getenv("OPENAI_API_KEY")

def complete_chat(
        messages: list[dict[str, str]],
        model="gpt-3.5-turbo",
        on_token: Callable[[int], None] = lambda p: None,
    ) -> str:
    responses = cast(
        Iterable[ChatCompletion],
        ChatCompletion.create(
            model=model,
            messages=messages,
            stream=True,
            temperature=0.0,
        ),
    )
    completion = ""

    for (i, partial) in enumerate(responses):
        delta = partial.choices[0].delta

        try:
            completion += str(delta.content)
        except AttributeError as error:
            pass

        on_token(i)

    return completion
