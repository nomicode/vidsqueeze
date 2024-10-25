from typing import List, Optional

import click

from . import runner


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
):
    """Compress video files"""
    if not input_files:
        click.echo("Error: No input files specified.", err=True)
        return

    if very_verbose:
        # Implied verbose mode
        verbose = True

    runner.process_files(
        input_files,
        no_audio,
        resolution,
        fps,
        lossless,
        quality,
        verbose,
        very_verbose,
    )


if __name__ == "__main__":
    main()
