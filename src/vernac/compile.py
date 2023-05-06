import argparse
import asyncio

from vernac.pipeline import VernacPipeline
from vernac.stages.all import (
    ReadSourceStage,
    MapModulesStage,
    RunPipelinesStage,
)

async def main(
        in_paths: list[str],
        out_path: str,
        injects_list: list[tuple[str, str]],
        verbose: bool = False,
        package_dir: str | None = None,
    ):
    pipeline = VernacPipeline(
        "start",
        [
            ReadSourceStage("Reading source"),
            MapModulesStage("Mapping modules"),
            RunPipelinesStage(
                out_path=out_path,
                injects=dict(injects_list),
                package_dir=package_dir,
            ),
        ],
        verbose=verbose,
    )

    await pipeline.run(dict(in_paths=in_paths))

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        dest="in_paths",
        metavar="PATH",
        nargs="+",
    )
    parser.add_argument(
        "-o",
        dest="out_path",
        metavar="PATH",
        required=True,
    )
    parser.add_argument(
        "-v",
        dest="verbose",
        action="store_true",
    )
    parser.add_argument(
        "--inject",
        metavar="PATH",
        dest="injects_list",
        nargs=2,
        action="append",
        default=[],
        help="use given source instead of generating (first pass only)"
    )
    parser.add_argument(
        "--package-dir",
        metavar="PATH",
        help="write package source here instead of temp dir",
    )

    args = parser.parse_args()

    return args

def script_main():
    main_kwargs = vars(parse_args())

    asyncio.run(main(**main_kwargs))

if __name__ == "__main__":
    script_main()
