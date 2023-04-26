import os
import os.path
import sys
import subprocess

from typing import BinaryIO
from subprocess import (
    check_output,
    CalledProcessError,
)
from tempfile import TemporaryDirectory

import tomli_w

from vernac.openai import complete_chat
from vernac.stages.interface import (
    VernacStage,
    StageContext,
    StageAction,
    StageOutput,
)

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

class PackageStage(VernacStage):
    steps = 2

    def __init__(self, title: str, out_path: str):
        self.title = title
        self.out_path = out_path

    def run(
            self,
            context: StageContext,
            python: str,
            dependencies: list[str],
            **kwargs,
        ) -> StageOutput:
        with TemporaryDirectory(prefix="vernac") as tmpdir:
            package_in_dir(python=python, dir_path=tmpdir, deps=dependencies)

            context.advance_progress()

            shiv_package(dir_path=tmpdir, out_path=self.out_path)

            context.advance_progress()

        return StageOutput(
            action=StageAction.NEXT,
            state=dict(out_path=self.out_path),
        )
