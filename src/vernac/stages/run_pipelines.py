from typing import Iterable

from vernac.pipeline import VernacPipeline
from vernac.stages.interface import (
    VernacStage,
    StageContext,
    StageAction,
    StageOutput,
)
from vernac.stages.all import (
    GenerateCodeStage,
    GuessDependenciesStage,
    PackageStage,
    CheckHelpStage,
    CheckTestsStage,
    DocumentModuleStage,
)
from vernac.stages.map_modules import SourceType

def build_common_stages(
        source_type: SourceType,
        verbose: bool = False,
        inject_first_path: str | None = None,
    ) -> list[VernacStage]:
    if inject_first_path is None:
        inject_first = None
    else:
        with open(inject_first_path) as inject_first_file:
            inject_first = inject_first_file.read()

    return [
        GenerateCodeStage(
            "Generating code",
            source_type=source_type,
            inject_first=inject_first,
            verbose=verbose,
        ),
        GuessDependenciesStage("Guessing dependencies"),
    ]

def build_module_stages(
        verbose: bool = False,
        inject_first_path: str | None = None,
    ) -> list[VernacStage]:
    stages = build_common_stages(
        source_type=SourceType.MODULE,
        verbose=verbose,
        inject_first_path=inject_first_path,
    )
    stages += [
        DocumentModuleStage("Documenting module"),
    ]

    return stages

def build_main_stages(
        out_path: str,
        verbose: bool = False,
        inject_first_path: str | None = None,
        package_dir: str | None = None,
    ) -> list[VernacStage]:
    stages = build_common_stages(
        source_type=SourceType.MAIN,
        verbose=verbose,
        inject_first_path=inject_first_path,
    )
    stages += [
        PackageStage(
            "Packaging",
            package_dir=package_dir,
            out_path=out_path,
        ),
        CheckHelpStage("Checking --help"),
        CheckTestsStage("Checking test output"),
    ]

    return stages

class RunPipelinesStage(VernacStage):
    def __init__(
            self,
            out_path: str,
            injects: dict[str, str],
            package_dir: str | None = None,
        ):
        self.out_path = out_path
        self.injects = injects
        self.package_dir = package_dir

    async def run(
            self,
            context: StageContext,
            english_all: dict[str, str],
            main_name: str,
            module_names: list[str],
        ) -> StageOutput:
        # build module pipelines
        module_pipelines: dict[str, VernacPipeline] = {}

        for name in module_names:
            module_stages = build_module_stages(
                verbose=context.verbose,
                inject_first_path=self.injects.get(name),
            )

            module_pipelines[name] = VernacPipeline(
                f"module_{name}",
                module_stages,
                logs_base_path=context.pipeline.logs_base_path,
                verbose=context.verbose,
            )

        # run module pipelines to completion
        modules: dict[str, dict] = {}

        for (name, pipeline) in module_pipelines.items():
            modules[name] = await pipeline.run(
                dict(vn_name=name, english=english_all[name]),
            )

        # build main pipeline
        main_stages = build_main_stages(
            out_path=self.out_path,
            verbose=context.verbose,
            inject_first_path=None,
            package_dir=self.package_dir,
        )
        main_pipeline = VernacPipeline(
            "main",
            main_stages,
            logs_base_path=context.pipeline.logs_base_path,
            verbose=context.verbose,
        )

        # run main pipeline to completion
        main = await main_pipeline.run(
            dict(
                english=english_all[main_name],
                modules=modules,
            )
        )

        return StageAction.NEXT.out()
