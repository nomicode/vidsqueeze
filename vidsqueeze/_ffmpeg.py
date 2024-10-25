import asyncio
import os
import re
import time
from typing import Dict, List, Optional, Tuple

from tqdm.asyncio import tqdm

from vidsqueeze import _console, _debug, _validator, exceptions

debug = _debug.debug


def _build_ffmpeg_command(
    input_file: str,
    output_file: str,
    no_audio: bool,
    resolution: Optional[str],
    fps: Optional[int],
    quality: Optional[int],
    very_verbose: bool,
) -> List[str]:
    """Build FFmpeg command with specified options."""
    ffmpeg_cmd = ["ffmpeg"]

    # Add verbosity flags
    if very_verbose:
        ffmpeg_cmd.extend(["-v", "info"])
    else:
        ffmpeg_cmd.extend(["-v", "error"])

    # Add input file
    ffmpeg_cmd.extend(["-i", input_file])

    # Add video codec and quality settings
    ffmpeg_cmd.extend(["-c:v", "libx264"])
    if quality is not None:
        ffmpeg_cmd.extend(["-crf", str(quality)])

    # Add resolution if specified
    if resolution:
        ffmpeg_cmd.extend(["-vf", f"scale=-2:{resolution[:-1]}"])

    # Add framerate if specified
    if fps:
        ffmpeg_cmd.extend(["-r", str(fps)])

    # Handle audio
    if no_audio:
        ffmpeg_cmd.extend(["-an"])
    else:
        ffmpeg_cmd.extend(["-c:a", "aac"])

    # Add progress pipe and output file
    ffmpeg_cmd.extend(["-progress", "pipe:1", "-y", output_file])

    debug.log(_debug.DebugCategory.FFMPEG, f"Command: {' '.join(ffmpeg_cmd)}")
    return ffmpeg_cmd


async def _probe_video(input_file: str) -> dict:
    """Asynchronously probe video file for information."""
    debug.log(_debug.DebugCategory.FFMPEG, f"Probing video: {input_file}")
    try:
        probe = await asyncio.create_subprocess_exec(
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            input_file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await probe.communicate()

        if probe.returncode != 0:
            error = stderr.decode()
            debug.log(_debug.DebugCategory.FFMPEG, f"Probe failed: {error}")
            raise exceptions.FFmpegProbeError(f"FFprobe failed: {error}") from None

        import json

        data = json.loads(stdout.decode())
        if not data.get("streams"):
            debug.log(
                _debug.DebugCategory.FFMPEG, "No video stream found in probe data"
            )
            raise exceptions.FFmpegProbeError("No video stream found") from None

        return data
    except Exception as e:
        debug.log(_debug.DebugCategory.FFMPEG, f"Probe error: {str(e)}")
        raise exceptions.FFmpegProbeError(f"Error probing video file: {str(e)}") from e


async def _get_video_info(
    input_file: str,
) -> Tuple[Optional[int], Optional[float], int]:
    """Get video frame count, duration, and file size."""
    try:
        data = await _probe_video(input_file)

        # Get file size
        file_size = os.path.getsize(input_file)

        # Find video stream
        video_stream = next(
            (s for s in data["streams"] if s["codec_type"] == "video"), None
        )
        if not video_stream:
            raise exceptions.FFmpegProbeError("No video stream found")

        # Get frame count and duration
        frames = None
        duration = None

        if "nb_frames" in video_stream:
            frames = int(video_stream["nb_frames"])
        if "duration" in video_stream:
            duration = float(video_stream["duration"])
        elif "duration" in data.get("format", {}):
            duration = float(data["format"]["duration"])

        debug.log(
            _debug.DebugCategory.FFMPEG,
            f"Video info - frames: {frames}, duration: {duration}s, size: {file_size} bytes",
        )
        return frames, duration, file_size

    except Exception as e:
        debug.log(_debug.DebugCategory.FFMPEG, f"Error getting video info: {str(e)}")
        raise exceptions.FFmpegError(f"Error getting video info: {e}") from e


async def _get_video_info_safe(
    input_file: str,
) -> Tuple[Optional[int], Optional[float], int]:
    """Safely get video information, returning None values on error."""
    try:
        return await _get_video_info(input_file)
    except Exception as e:
        debug.log(_debug.DebugCategory.FFMPEG, f"Error getting video info: {str(e)}")
        _console.print_error(f"Error getting video info: {e}")
        return None, None, 0


async def _compress_single_file(
    input_file: str,
    info: "VideoInfo",
    output_suffix: str,
    no_audio: bool,
    resolution: Optional[str],
    fps: Optional[str],
    quality: Optional[int],
    very_verbose: bool,
    position: int,
) -> None:
    """Compress a single video file."""
    try:
        debug.log(_debug.DebugCategory.FFMPEG, f"Compressing file: {input_file}")
        base = os.path.splitext(input_file)[0]
        ext = os.path.splitext(input_file)[1]
        output_file = f"{base}{output_suffix}{ext}"

        # Create progress bar for this file
        pbar = tqdm(
            total=info.frames,
            desc=f"Compressing {os.path.basename(input_file)}",
            unit="frames",
            position=position,
            leave=False,
        )

        # Run FFmpeg process
        process = await asyncio.create_subprocess_exec(
            *_build_ffmpeg_command(
                input_file=input_file,
                output_file=output_file,
                no_audio=no_audio,
                resolution=resolution,
                fps=int(fps) if fps else None,
                quality=quality,
                very_verbose=very_verbose,
            ),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Track progress
        last_frame = 0
        while True:
            if process.stdout is None:
                break

            try:
                line = await process.stdout.readline()
                if not line:
                    break

                line = line.decode().strip()

                # Parse progress information
                if line.startswith("frame="):
                    current_frame = int(line.split("=")[1])
                    if current_frame > last_frame:
                        pbar.update(current_frame - last_frame)
                        last_frame = current_frame

            except Exception as e:
                debug.log(_debug.DebugCategory.FFMPEG, f"Progress error: {str(e)}")
                break

        # Wait for process to complete
        await process.wait()

        # Close progress bar
        pbar.close()

        if process.returncode != 0:
            stderr = await process.stderr.read()
            error = stderr.decode()
            debug.log(_debug.DebugCategory.FFMPEG, f"Encoding failed: {error}")
            _console.print_error("Encoding failed")
            raise exceptions.FFmpegError("Encoding failed")

        # Validate output file
        debug.log(
            _debug.DebugCategory.VALIDATION, f"Validating output file: {output_file}"
        )
        validation = await _validator.validate_file(output_file)
        if not validation.is_valid:
            raise exceptions.FFmpegError(
                f"Output validation failed: {validation.error_message}"
            )

    except Exception as e:
        debug.log(
            _debug.DebugCategory.FFMPEG,
            f"Error compressing file {input_file}: {str(e)}",
        )
        _console.print_error(f"Error compressing file {input_file}: {str(e)}")
        raise


async def probe_files(
    valid_files: List[str],
    max_jobs: int,
    verbose: bool,
) -> Dict[str, "VideoInfo"]:
    """Probe multiple video files concurrently."""
    debug.log(
        _debug.DebugCategory.FFMPEG,
        f"Starting probe phase with {len(valid_files)} files",
    )
    if verbose:
        _console._print_status("Phase 2", "Probing video files")

    async def probe_file(file: str) -> tuple[str, Optional["VideoInfo"]]:
        try:
            debug.log(_debug.DebugCategory.FFMPEG, f"Probing file: {file}")
            frames, duration, size = await _get_video_info_safe(file)
            if frames is not None:
                from vidsqueeze.runner import VideoInfo

                return file, VideoInfo(file, frames, duration, size)
        except Exception as e:
            debug.log(
                _debug.DebugCategory.FFMPEG, f"Error probing file {file}: {str(e)}"
            )
            _console.print_error(f"Error probing file {file}: {str(e)}")
        return file, None

    # Process files with progress bar
    results = {}
    tasks = [probe_file(f) for f in valid_files]
    for file, info in await asyncio.gather(*tasks):
        if info is not None:
            results[file] = info

    if verbose:
        _console._print_status(
            "Probe Complete",
            f"Successfully probed {len(results)} of {len(valid_files)} files",
        )

    debug.log(_debug.DebugCategory.FFMPEG, "Probe phase complete")
    return results


async def compress_files(
    video_infos: Dict[str, "VideoInfo"],
    output_suffix: str,
    max_jobs: int,
    no_audio: bool,
    resolution: Optional[str],
    fps: Optional[str],
    quality: Optional[int],
    verbose: bool,
    very_verbose: bool,
) -> None:
    """Compress multiple video files concurrently."""
    debug.log(
        _debug.DebugCategory.FFMPEG,
        f"Starting compression phase with {len(video_infos)} files",
    )
    if verbose:
        _console._print_status("Phase 3", "Compressing video files")

    # Create compression tasks
    tasks = []
    for i, (file, info) in enumerate(video_infos.items()):
        task = _compress_single_file(
            file,
            info,
            output_suffix,
            no_audio,
            resolution,
            fps,
            quality,
            very_verbose,
            position=i % max_jobs,  # Cycle positions based on max_jobs
        )
        tasks.append(task)

    # Process files with semaphore
    semaphore = asyncio.Semaphore(max_jobs)

<<<<<<< Updated upstream
    if very_verbose:
        _console._print_status("FFmpeg command", " ".join(ffmpeg_cmd))
=======
    async def process_with_semaphore(task):
        async with semaphore:
            return await task
>>>>>>> Stashed changes

    await asyncio.gather(*[process_with_semaphore(task) for task in tasks])

    if verbose:
        _console._print_status(
            "Compression Complete", f"Processed {len(video_infos)} files"
        )

    debug.log(_debug.DebugCategory.FFMPEG, "Compression phase complete")
