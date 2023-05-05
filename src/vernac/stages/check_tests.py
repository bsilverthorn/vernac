import os
import subprocess
import json

from subprocess import (
    check_output,
    CalledProcessError,
)

from vernac.util import normalize_progress
from vernac.openai import complete_chat
from vernac.stages.interface import (
    VernacStage,
    StageContext,
    StageAction,
    StageOutput,
)
from vernac.stages.generate_code import TestFailure

def extract_suggested_tests(context: StageContext, english: str) -> list[dict]:
    # prepare prompt
    system_prompt = """
You are an expert programmer working on contract. The user, your client, will provide a description of program functionality. You will provide details of how to execute any tests listed in the spec. Relevant documentation might also be provided, but should be ignored. Only look at tests included with the program spec, not in any documentation.

For each test listed in the spec, extract the arguments to run along with any description of correct output. List that information a single line of JSON in the following format:

{"args": "--foo -x=bar", "description": "should print 10 lines"}

Do not list the name of the program itself, only the arguments. If no tests are listed, write nothing.
"""
    user_prompt = (
        f"# Program Spec\n\n{english}"
    )
    chat_messages = [
        {"role": "system", "content": system_prompt.strip()},
        {"role": "user", "content": user_prompt.strip()},
    ]

    context.log_json("prompt.json", chat_messages)

    # run the prompt and extract tests
    def on_token(i: int):
        context.update_progress(completed=normalize_progress(i))

    chat_completion = complete_chat(
        chat_messages,
        model="gpt-4",
        on_token=on_token,
    )

    context.log_text("completion.txt", chat_completion)

    test_args = [json.loads(v) for v in chat_completion.splitlines() if v.strip()]

    context.log_json("test_args.json", test_args)

    return test_args

def evaluate_test_output(
        context: StageContext,
        english: str,
        program_args: list[str],
        output: str,
        expectation: str,
    ) -> str | None:
    # prepare prompt
    system_prompt = """
You are an expert programmer working on contract. The user, your client, will provide a description of program functionality along with output from a test. You will decide whether the test output is correct.

If the test output is incorrect, write a one-line description of the problem.

If the test output is correct, write nothing.
"""
    user_prompt = (
        f"# Program Spec\n\n{english}\n\n"
        "# Test output\n\n"
        f'Expectation: "{expectation}"\n\n'
        f"Output:\n\n```$ ./program {' '.join(program_args)}\n{output}```\n\n"
    )
    chat_messages = [
        {"role": "system", "content": system_prompt.strip()},
        {"role": "user", "content": user_prompt.strip()},
    ]

    context.log_json("eval_prompt.json", chat_messages)

    # run the prompt and extract tests
    def on_token(i: int):
        context.update_progress(completed=normalize_progress(i))

    chat_completion = complete_chat(
        chat_messages,
        model="gpt-4",
        on_token=on_token,
    )

    context.log_text("eval_completion.txt", chat_completion)

    if chat_completion.strip() == "":
        return None
    else:
        return chat_completion

def check_suggested_test(
        context: StageContext,
        english: str,
        program_path: str,
        program_args: list[str],
        expectation: str,
    ) -> TestFailure | None:
    try:
        output = check_output(
            [program_path] + program_args,
            stderr=subprocess.STDOUT,
            timeout=16.0,
        )
    except CalledProcessError as error:
        context.log_bytes("output.txt", error.output)

        description = error.output.decode("utf-8") + f"\n<exit code {error.returncode}>"

        return TestFailure(
            input=f"Ran program with `{' '.join(program_args)}`.",
            expected=expectation,
            actual=description,
        )
    else:
        context.log_bytes("output.txt", output)

        description = evaluate_test_output(
            context,
            english=english,
            program_args=program_args,
            output=output.decode("utf-8"),
            expectation=expectation,
        )

        if description is None:
            return None
        else:
            return TestFailure(
                input=f"Ran program with `{' '.join(program_args)}`.",
                expected=expectation,
                actual=description,
            )

class CheckTestsStage(VernacStage):
    steps = 100

    def __init__(self, title: str):
        self.title = title

    def run(
            self,
            context: StageContext,
            english: str,
            python: str,
            out_path: str,
            test_failures: list[TestFailure] = [],
            **kwargs,
        ) -> StageOutput:
        program_path = os.path.abspath(out_path)
        suggested_tests = extract_suggested_tests(context, english)
        test_failures = list(test_failures)

        for suggested_test in suggested_tests:
            failure = check_suggested_test(
                context,
                english=english,
                program_path=program_path,
                program_args=suggested_test["args"].split(),
                expectation=suggested_test["description"],
            )

            if failure is not None:
                test_failures.append(failure)

        context.log_json(
            "failures.json",
            [f.__dict__ for f in test_failures],
        )

        return StageOutput(
            action=StageAction.NEXT if len(test_failures) == 0 else StageAction.LOOP,
            state=dict(test_failures=test_failures, first_draft=python),
        )
