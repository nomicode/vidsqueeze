import asyncio
import os
from typing import Dict, List, Optional

from . import _console, _ffmpeg, _validator
from ._debug import DebugCategory, debug, log_call

# Default maximum number of concurrent jobs
MAX_JOBS = 8


def calc_max_jobs() -> int:
    """Calculate the maximum number of concurrent jobs based on CPU cores."""
    try:
        return os.cpu_count() or MAX_JOBS
    except Exception:
        return MAX_JOBS


class VideoInfo:
    def __init__(self, path: str, frames: int, duration: float, size: int):
        self.path = path
        self.frames = frames
        self.duration = duration
        self.size = size


@log_call(DebugCategory.VALIDATION)
async def validate_files(
    input_files: List[str],
    verbose: bool,
) -> Dict[str, _validator.ValidationResult]:
    """Phase 1: Validate all input files."""
    debug.log(
        DebugCategory.VALIDATION,
        f"Starting validation phase with {len(input_files)} files",
    )
    if verbose:
        _console._print_status("Phase 1", "Validating input files")

    results = await _validator.validate_files(input_files, verbose)

    if verbose:
        valid_count = sum(1 for r in results.values() if r.is_valid)
        _console._print_status(
            "Validation Complete", f"Found {valid_count} valid video files"
        )

    debug.log(DebugCategory.VALIDATION, "Validation phase complete")
    return results


@log_call(DebugCategory.CLI)
def process_files(
    input_files: List[str],
    no_audio: bool,
    resolution: Optional[str],
    fps: Optional[str],
    lossless: bool,
    quality: Optional[int],
    verbose: bool,
    very_verbose: bool,
    max_jobs: Optional[int] = None,
) -> None:
    """Process video files in three phases: validate, probe, and compress."""
    debug.log(DebugCategory.CLI, "Starting file processing")

    # Determine max jobs
    actual_max_jobs = max_jobs or calc_max_jobs()
    debug.log(DebugCategory.CLI, f"Using {actual_max_jobs} max jobs")

    # Build output suffix
    suffix_parts = ["-ffmpeg"]
    if no_audio:
        suffix_parts.append("-n")
    if resolution:
        suffix_parts.append(f"-r{resolution}")
    if fps:
        suffix_parts.append(f"-f{fps}")
    if lossless:
        suffix_parts.append("-lossless")
    if quality is not None:
        suffix_parts.append(f"-q{quality}")
    output_suffix = "".join(suffix_parts)
    debug.log(DebugCategory.CLI, f"Using output suffix: {output_suffix}")

    async def main():
        # Phase 1: Validate files
        validation_results = await validate_files(input_files, verbose)
        valid_files = [f for f, r in validation_results.items() if r.is_valid]

        if not valid_files:
            debug.log(DebugCategory.CLI, "No valid video files found")
            _console.print_error("No valid video files found")
            return

        # Phase 2: Probe files
        video_infos = await _ffmpeg.probe_files(valid_files, actual_max_jobs, verbose)

        if not video_infos:
            debug.log(DebugCategory.CLI, "No files successfully probed")
            _console.print_error("No files successfully probed")
            return

        # Phase 3: Compress files
        await _ffmpeg.compress_files(
            video_infos,
            output_suffix,
            actual_max_jobs,
            no_audio,
            resolution,
            fps,
            quality,
            verbose,
            very_verbose,
        )

    debug.log(DebugCategory.CLI, "Running main async process")
    asyncio.run(main())
    debug.log(DebugCategory.CLI, "Processing complete")
