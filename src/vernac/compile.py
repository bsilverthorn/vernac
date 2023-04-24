import os
import os.path
import math
import sys
import argparse
import subprocess

from typing import (
    cast,
    BinaryIO,
    Iterable,
)
from subprocess import (
    check_output,
    CalledProcessError,
)
from tempfile import TemporaryDirectory
from dataclasses import dataclass

import openai
import tomli_w

from rich import print as rich_print
from rich.markup import escape
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)
from openai import ChatCompletion

from vernac.util import strip_markdown_fence

progress = Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    TaskProgressColumn(),
)
openai.api_key = os.getenv("OPENAI_API_KEY")

def print(*args, **kwargs):
    def yield_args():
        for arg in args:
            if isinstance(arg, str):
                yield escape(arg)
            else:
                yield arg

    rich_print(*yield_args(), **kwargs)

def normalize_progress(x, scale=100, divisor=32, max_y=0.99):
    return scale * min(
        max_y,
        (1 - math.exp(-x / divisor)),
    )

def complete_chat(messages: list[dict], model="gpt-3.5-turbo", task_title=None):
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

    if task_title is None:
        task = None
    else:
        task = progress.add_task(task_title, total=100)

    for (i, partial) in enumerate(responses):
        delta = partial.choices[0].delta

        try:
            completion += str(delta.content)
        except AttributeError as error:
            pass

        if task is not None:
            progress.update(task, completed=normalize_progress(i))

    if task is not None:
        progress.update(task, completed=100)

    return completion

def get_dependencies(python: str) -> list[str]:
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
    chat_completion = complete_chat(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        model="gpt-4",
        task_title="Analyzing",
    )
    dependencies = set(chat_completion.splitlines()) - sys.stdlib_module_names

    return list(dependencies)

@dataclass
class TestFailure:
    input: str
    expected: str
    actual: str

def compile(
        english: str,
        first_draft: str | None = None,
        test_failures: list[TestFailure] = [],
    ) -> str:
    system_prompt = (
        "You are an expert programmer working on contract. "
        "The user, your client, will provide a description of program functionality. "
        "Respond with Python 3 source code implementing that description. " 
        "Respond only with the source code inside a Markdown code block. "
        "Do not add commentary."
    )
    user_prompt = (
        "Please write the following program in Python 3. "
        "Include a `main` function that takes no arguments and returns nothing. "
        "Use `argparse` to parse command line arguments."
        f"\n\n# Program Spec\n\n{english}\n"
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
    chat_completion = complete_chat(chat_messages, task_title="Compiling", model="gpt-4")
    python = strip_markdown_fence(chat_completion)

    return python

def generate_pyproject(file: BinaryIO, deps: list[str]):
    data = {
        "build-system": {
            "requires": ["setuptools", "setuptools-scm"],
            "build-backend": "setuptools.build_meta"
        },
        "project": {
            "name": "compiled_by_vernac",
            "requires-python": ">=3.10",
            "dependencies": deps,
            "version": "0.0.1",
            "scripts": {
                "main": "compiled_by_vernac.main:main"
            },
        },
    }
    
    tomli_w.dump(data, file)

def package_in_dir(python: str, dir_path: str, deps: list[str]):
    def to_dir(rel_path: str) -> str:
        return os.path.join(dir_path, rel_path)

    os.makedirs(to_dir("src/compiled_by_vernac"))

    with open(to_dir("src/compiled_by_vernac/main.py"), "w") as file:
        file.write(python)

    with open(to_dir("pyproject.toml"), "wb") as file:
        generate_pyproject(file, deps)

def shiv_package(dir_path: str, out_path: str):
    # crudely guess the shiv bin location
    python_dir = os.path.dirname(sys.executable)
    shiv_path = os.path.join(python_dir, "shiv")

    # run shiv to package
    try:
        check_output(
            [
                shiv_path,
                "-o", out_path,
                "-c", "main",
                dir_path,
            ],
            stderr=subprocess.STDOUT,
        )
    except CalledProcessError as error:
        print(error.output)

        raise

def package(python: str, out_path: str, deps: list[str]):
    task = progress.add_task("Packaging", total=2)

    with TemporaryDirectory(prefix="vernac") as tmpdir:
        package_in_dir(python=python, dir_path=tmpdir, deps=deps)

        progress.update(task, advance=1)

        shiv_package(dir_path=tmpdir, out_path=out_path)

        progress.update(task, advance=1)

def assess_run_help(out_path: str) -> list[TestFailure]:
    try:
        output = check_output(
            [
                os.path.abspath(out_path),
                "--help",
            ],
            stderr=subprocess.STDOUT,
        )
    except CalledProcessError as error:
        return [
            TestFailure(
                input="Ran program with `--help`.",
                expected="Standard help text",
                actual=error.output,
            ),
        ]
    else:
        return []

def main(in_path: str, out_path: str, verbose: bool = False):
    test_failures = None
    first_draft = None
    passes = 0

    with progress:
        while test_failures != []:
            if passes > 4:
                raise Exception("too many passes")

            task = progress.add_task("Reading", total=1)

            with open(in_path, "r") as f:
                src = f.read()

            progress.update(task, advance=1)

            if test_failures is None:
                test_failures = []

            python = compile(
                src,
                first_draft=first_draft,
                test_failures=test_failures,
            )

            if verbose:
                print("# Source", "\n\n```\n", python, "```")

            deps = get_dependencies(python)

            if verbose:
                print("\n# Dependencies\n", deps)

            package(python, out_path, deps)

            test_failures = assess_run_help(out_path)
            first_draft = python
            passes += 1

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
