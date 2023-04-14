import os
import os.path
import math
import re
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

import openai
import tomli_w

from rich import print
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)
from openai import ChatCompletion

progress = Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    TaskProgressColumn(),
)
openai.api_key = os.getenv("OPENAI_API_KEY")

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

def strip_markdown_fence(markdown: str) -> str:
    pattern = r"```\s*\w*\s*\n(?P<inner>.*?)```"
    match = re.search(pattern, markdown, re.DOTALL)

    if match:
        inner = match.group("inner")
    else:
        inner = markdown

    return inner.strip() + "\n"

def get_dependencies(python: str) -> list[str]:
    system_prompt = (
        "You are an expert programmer working on contract. "
        "The user, your client, will share a Python program. "
        "Respond with a list of Python packages that must be installed to run the program. "
        "Standard library packages do not need to be installed and should be ignored. "
        "Write one package per line. "
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

def compile(english: str):
    system_prompt = (
        "You are an expert programmer working on contract. "
        "The user, your client, will provide a description of program functionality. "
        "Respond with Python 3 source code implementing that description. " 
        "Respond only with the source code inside a Markdown code block. "
        "Do not add commentary."
    )
    user_prompt = (
        "Please write the following program in Python 3. "
        "Include a `main` function that takes no arguments and returns nothing."
        f"\n\n# Program Spec\n\n{english}\n"
    )
    chat_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    chat_completion = complete_chat(chat_messages, task_title="Compiling")
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

def main(in_path: str, out_path: str, verbose: bool = False):

    with progress:
        task = progress.add_task("Reading", total=1)

        with open(in_path, "r") as f:
            src = f.read()

        progress.update(task, advance=1)

        python = compile(src)

        if verbose:
            print("# Source", "\n\n```\n", python, "```")

        deps = get_dependencies(python)

        if verbose:
            print("\n# Dependencies\n", deps)

        package(python, out_path, deps)

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
