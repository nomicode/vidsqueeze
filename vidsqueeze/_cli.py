import sys
from typing import List, Optional

import click

from . import _console, _debug, runner

debug = _debug.debug


@click.command()
@click.option("-n", "--no-audio", is_flag=True, help="No audio")
@click.option(
    "-r",
    "--resolution",
    type=click.Choice(["4k", "1080p", "720p", "576p", "480p"]),
    help="Resolution",
)
@click.option(
    "-f",
    "--fps",
    type=str,
    help="Frame rate (film=24, pal=25, ntsc=30, 60fps=60, or custom number)",
)
@click.option("-l", "--lossless", is_flag=True, help="Lossless mode")
@click.option(
    "-q",
    "--quality",
    type=click.IntRange(0, 51),
    help="CRF quality (0-51, lower is better, 23 is default)",
)
@click.option("-v", "--verbose", is_flag=True, help="Verbose mode")
@click.option("-vv", "--very-verbose", is_flag=True, help="Very verbose mode")
@click.option(
    "-j",
    "--jobs",
    type=int,
    default=runner.calc_max_jobs(),
    show_default=True,
    help="Maximum number of concurrent jobs",
)
@click.argument("input_files", nargs=-1, type=click.Path(exists=True))
def main(
    input_files: List[str],
    no_audio: bool,
    resolution: Optional[str],
    fps: Optional[str],
    lossless: bool,
    quality: Optional[int],
    verbose: bool,
    very_verbose: bool,
    jobs: int,
):
    """Compress video files"""
    debug.log(_debug.DebugCategory.CLI, "CLI entry point")
    debug.log(_debug.DebugCategory.CLI, f"Input files: {input_files}")
    debug.log(
        _debug.DebugCategory.CLI,
        f"Options: no_audio={no_audio}, resolution={resolution}, fps={fps}",
    )
    debug.log(
        _debug.DebugCategory.CLI,
        f"verbose={verbose}, very_verbose={very_verbose}, jobs={jobs}",
    )

    try:
        if not input_files:
            debug.log(_debug.DebugCategory.CLI, "No input files specified")
            _console.print_error("No input files specified.")
            sys.exit(1)

        if very_verbose:
            verbose = True

        debug.log(_debug.DebugCategory.CLI, "Starting runner.process_files")
        runner.process_files(
            input_files,
            no_audio,
            resolution,
            fps,
            lossless,
            quality,
            verbose,
            very_verbose,
            max_jobs=jobs,
        )
        debug.log(_debug.DebugCategory.CLI, "Runner.process_files completed")

    except Exception as e:
        debug.log(_debug.DebugCategory.CLI, f"Fatal error in CLI: {str(e)}")
        import traceback

        traceback.print_exc()
        _console.print_error(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
