import asyncio
import os
import re
import sys
import time
from typing import Optional

import ffmpeg

from . import _console, _pbar, _units, exceptions


def _build_ffmpeg_command(
    input_file: str,
    output_file: str,
    no_audio: bool,
    resolution: Optional[str],
    fps: Optional[str],
    lossless: bool,
    quality: Optional[int],
) -> list:
    ffmpeg_cmd = [
        "ffmpeg",
        "-i",
        input_file,
        "-progress",
        "pipe:1",
        "-nostats",
    ]

    if no_audio:
        ffmpeg_cmd.append("-an")
    else:
        ffmpeg_cmd.extend(["-c:a", "aac", "-b:a", "128k"])

    if resolution:
        scale_filter = _get_scale_filter(resolution)
        if scale_filter:
            ffmpeg_cmd.extend(["-vf", scale_filter])

    if fps:
        fps_value = _get_fps_value(fps)
        ffmpeg_cmd.extend(["-r", str(fps_value)])

    _configure_video_codec(ffmpeg_cmd, lossless, quality)

    ffmpeg_cmd.append("-y")
    ffmpeg_cmd.append(output_file)

    return ffmpeg_cmd


def _get_scale_filter(resolution: str) -> Optional[str]:
    return {
        "4k": "scale=min(3840\\,iw):min(2160\\,ih):force_original_aspect_ratio=decrease",
        "1080p": "scale=min(1920\\,iw):min(1080\\,ih):force_original_aspect_ratio=decrease",
        "720p": "scale=min(1280\\,iw):min(720\\,ih):force_original_aspect_ratio=decrease",
        "576p": "scale=min(1024\\,iw):min(576\\,ih):force_original_aspect_ratio=decrease",
        "480p": "scale=min(854\\,iw):min(480\\,ih):force_original_aspect_ratio=decrease",
    }.get(resolution)


def _get_fps_value(fps: str) -> int:
    return {"film": 24, "pal": 25, "ntsc": 30, "60fps": 60}.get(fps, fps)


def _configure_video_codec(ffmpeg_cmd: list, lossless: bool, quality: Optional[int]):
    if lossless:
        ffmpeg_cmd.extend(["-c:v", "libx264", "-preset", "medium", "-crf", "0"])
    else:
        quality_value = quality if quality is not None else 23
        ffmpeg_cmd.extend(
            ["-c:v", "libx264", "-preset", "medium", "-crf", str(quality_value)]
        )


def _ffprobe(input_file):
    probe = ffmpeg.probe(input_file)
    video_stream = next(
        (stream for stream in probe["streams"] if stream["codec_type"] == "video"),
        None,
    )
    if video_stream is None:
        raise exceptions.FFmpegProbeError("No video stream found")

    fps_string = video_stream["r_frame_rate"]
    fps_numerator, fps_denominator = map(int, fps_string.split("/"))
    fps = fps_numerator / fps_denominator  # Calculate the actual FPS
    duration = float(video_stream["duration"])
    total_frames = int(fps * duration)
    file_size = os.path.getsize(input_file)
    return total_frames, duration, file_size


def _get_video_info(input_file):
    try:
        return _ffprobe(input_file)
    except ffmpeg.Error as e:
        _console.print_error(f"Error probing video file: {e}")
        sys.exit(1)
    except Exception as e:
        _console.print_error(f"An unexpected error occurred: {e}")
        sys.exit(1)


async def _get_video_info_safe(input_file: str):
    try:
        return _get_video_info(input_file)
    except Exception as e:
        _console.print_error(f"Error getting video info: {e}")
        return None, None, None


async def _track_progress(process, input_file: str, duration: float, file_size: int):
    # Get the progress bar for this file
    pbar = _pbar.get_file_pbar(input_file, file_size)
    last_progress = 0

    time_regex = re.compile(r"out_time_ms=(\d+)")
    async for line in process.stdout:
        line = line.decode()
        if time_match := time_regex.search(line):
            time_ms = int(time_match[1])
            progress = int(time_ms / (duration * 1000000) * file_size)
            progress_diff = progress - last_progress
            if progress_diff > 0:
                _pbar.update_pbar(input_file, progress_diff)
                last_progress = progress

    # Update to 100% if not already there
    remaining = file_size - last_progress
    if remaining > 0:
        _pbar.update_pbar(input_file, remaining)


async def _handle_process_completion(
    process,
    output_file: str,
    stdout: bytes,
    stderr: bytes,
    start_time: float,
    file_size: int,
    verbose: bool,
    very_verbose: bool,
):
    elapsed_time = time.time() - start_time
    avg_speed = file_size / elapsed_time / 1024 / 1024  # MB/s

    if verbose:
        _console._print_status("Wrote", output_file)

    if very_verbose:
        data_volume_str = _units._format_data_volume(file_size)
        time_str = _units._format_time(elapsed_time)
        data_rate_str = _units._format_data_rate(avg_speed)
        _console._print_status(
            "Compressed",
            f"{data_volume_str} in {time_str} at {data_rate_str}",
        )

    if process.returncode != 0:
        _console.print_error("Encoding failed")
        _console.print_error(f"FFmpeg error output:\n{stderr.decode()}")
        sys.exit(1)


async def _run_ffmpeg_process(
    ffmpeg_cmd: list,
    input_file: str,
    output_file: str,
    duration: float,
    file_size: int,
    verbose: bool,
    very_verbose: bool,
):
    process = await asyncio.create_subprocess_exec(
        *ffmpeg_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    start_time = time.time()

    await _track_progress(process, input_file, duration, file_size)

    stdout, stderr = await process.communicate()
    await _handle_process_completion(
        process,
        output_file,
        stdout,
        stderr,
        start_time,
        file_size,
        verbose,
        very_verbose,
    )


async def _compress_video(
    input_file: str,
    output_file: str,
    no_audio: bool,
    resolution: Optional[str],
    fps: Optional[str],
    lossless: bool,
    quality: Optional[int],
    verbose: bool,
    very_verbose: bool,
):
    if verbose:
        _console._print_status("Compressing", input_file)

    total_frames, duration, file_size = await _get_video_info_safe(input_file)

    ffmpeg_cmd = _build_ffmpeg_command(
        input_file, output_file, no_audio, resolution, fps, lossless, quality
    )

    if very_verbose:
        _console._print_status("FFmpeg command", " ".join(ffmpeg_cmd))

    await _run_ffmpeg_process(
        ffmpeg_cmd, input_file, output_file, duration, file_size, verbose, very_verbose
    )
