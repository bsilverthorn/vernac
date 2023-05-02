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
from itertools import chain
from contextlib import nullcontext

import tomli_w

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
            "name": "vnprog",
            "requires-python": ">=3.10",
            "dependencies": deps,
            "version": "0.0.1",
            "scripts": {
                "main": "vnprog.main:main"
            },
        },
    }

    tomli_w.dump(data, file)

def package_in_dir(py_files: dict[str, str], dir_path: str, deps: list[str]):
    def to_dir(*rel_paths: str) -> str:
        return os.path.join(dir_path, *rel_paths)

    os.makedirs(to_dir("src/vnprog"), exist_ok=True)

    for (filename, python) in py_files.items():
        py_path = to_dir("src/vnprog", filename)

        with open(py_path, "wt") as file:
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

    def __init__(
            self,
            title: str,
            out_path: str,
            package_dir: str | None = None,
        ):
        self.title = title
        self.out_path = out_path
        self.package_dir = package_dir

    def run(
            self,
            context: StageContext,
            python: str,
            dependencies: list[str],
            modules: dict[str, dict],
        ) -> StageOutput:
        py_files = {"main.py": python}

        for module in modules.values():
            py_files[module["py_name"]] = module["python"]

        module_deps = chain.from_iterable(
            m["dependencies"] for m in modules.values()
        )

        if self.package_dir is None:
            tmpdir_context = TemporaryDirectory(prefix="vernac-")
        else:
            tmpdir_context = nullcontext(
                os.path.abspath(self.package_dir),
            )

        with tmpdir_context as tmpdir:
            package_in_dir(
                py_files=py_files,
                dir_path=tmpdir,
                deps=dependencies + list(module_deps),
            )

            context.advance_progress()

            shiv_package(dir_path=tmpdir, out_path=self.out_path)

        context.advance_progress()

        return StageOutput(
            action=StageAction.NEXT,
            state=dict(out_path=self.out_path),
        )
