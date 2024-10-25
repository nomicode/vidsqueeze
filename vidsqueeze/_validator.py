import asyncio
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from vidsqueeze import _console, _debug

debug = _debug.debug


@dataclass
class ValidationResult:
    """Result of file validation."""

    is_valid: bool
    error_message: Optional[str] = None
    file_size: Optional[int] = None


async def _check_file_exists(path: str) -> Tuple[bool, Optional[str]]:
    """Check if file exists and is a regular file."""
    debug.log(_debug.DebugCategory.VALIDATION, f"Checking file exists: {path}")
    try:
        if not os.path.exists(path):
            debug.log(_debug.DebugCategory.VALIDATION, f"File does not exist: {path}")
            return False, "File does not exist"
        if not os.path.isfile(path):
            debug.log(_debug.DebugCategory.VALIDATION, f"Not a regular file: {path}")
            return False, "Not a regular file"

        debug.log(_debug.DebugCategory.VALIDATION, f"File exists: {path}")
        return True, None
    except Exception as e:
        debug.log(_debug.DebugCategory.VALIDATION, f"Error checking file: {str(e)}")
        return False, f"Error checking file: {str(e)}"


async def _check_file_size(path: str) -> Tuple[bool, Optional[str], int]:
    """Check if file has non-zero size."""
    debug.log(_debug.DebugCategory.VALIDATION, f"Checking file size: {path}")
    try:
        size = os.path.getsize(path)
        if size == 0:
            debug.log(_debug.DebugCategory.VALIDATION, f"File is empty: {path}")
            return False, "File is empty", 0

        debug.log(
            _debug.DebugCategory.VALIDATION, f"File size OK: {path} ({size} bytes)"
        )
        return True, None, size
    except Exception as e:
        debug.log(
            _debug.DebugCategory.VALIDATION, f"Error checking file size: {str(e)}"
        )
        return False, f"Error checking file size: {str(e)}", 0


async def _check_video_format(path: str) -> Tuple[bool, Optional[str]]:
    """Check if file is a valid video using ffprobe."""
    debug.log(_debug.DebugCategory.VALIDATION, f"Checking video format: {path}")
    try:
        debug.log(_debug.DebugCategory.VALIDATION, f"Running ffprobe: {path}")
        process = await asyncio.create_subprocess_exec(
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error = stderr.decode().strip()
            debug.log(_debug.DebugCategory.VALIDATION, f"FFprobe error: {error}")
            return False, f"FFprobe error: {error}"

        import json

        data = json.loads(stdout.decode())
        if not data.get("streams"):
            debug.log(
                _debug.DebugCategory.VALIDATION, f"No video streams found: {path}"
            )
            return False, "No video streams found"

        debug.log(_debug.DebugCategory.VALIDATION, f"Valid video format: {path}")
        return True, None
    except Exception as e:
        debug.log(
            _debug.DebugCategory.VALIDATION, f"Error validating video format: {str(e)}"
        )
        return False, f"Error validating video format: {str(e)}"


async def validate_file(path: str) -> ValidationResult:
    """Run all validation checks on a file."""
    debug.log(_debug.DebugCategory.VALIDATION, f"Starting validation for: {path}")

    exists_ok, exists_err = await _check_file_exists(path)
    if not exists_ok:
        debug.log(
            _debug.DebugCategory.VALIDATION, f"File exists check failed: {exists_err}"
        )
        return ValidationResult(False, exists_err)

    size_ok, size_err, file_size = await _check_file_size(path)
    if not size_ok:
        debug.log(
            _debug.DebugCategory.VALIDATION, f"File size check failed: {size_err}"
        )
        return ValidationResult(False, size_err)

    video_ok, video_err = await _check_video_format(path)
    if not video_ok:
        debug.log(
            _debug.DebugCategory.VALIDATION, f"Video format check failed: {video_err}"
        )
        return ValidationResult(False, video_err)

    debug.log(_debug.DebugCategory.VALIDATION, f"All validation passed for: {path}")
    return ValidationResult(True, None, file_size)


async def validate_files(
    input_files: List[str], verbose: bool = False
) -> Dict[str, ValidationResult]:
    """Validate multiple files and return results."""
    debug.log(
        _debug.DebugCategory.VALIDATION,
        f"Starting batch validation of {len(input_files)} files",
    )
    debug.log(_debug.DebugCategory.VALIDATION, f"Files to validate: {input_files}")

    results = {}
    valid_count = 0
    total_count = len(input_files)

    for file in input_files:
        result = await validate_file(file)
        results[file] = result

        status = "Valid" if result.is_valid else f"Invalid: {result.error_message}"
        debug.log(
            _debug.DebugCategory.VALIDATION, f"Validation result for {file}: {status}"
        )
        if verbose:
            _console._print_status(os.path.abspath(file), status)

        if result.is_valid:
            valid_count += 1

    # Log summary
    debug.log(
        _debug.DebugCategory.VALIDATION,
        f"Validation summary: {valid_count}/{total_count} valid files",
    )
    if verbose:
        _console._print_status(
            "Valid files",
            f"{valid_count} out of {total_count} ({valid_count/total_count:.1%})",
        )

    # Log invalid files if any
    invalid_files = [file for file, result in results.items() if not result.is_valid]
    if invalid_files and verbose:
        debug.log(_debug.DebugCategory.VALIDATION, "Invalid files:")
        _console._print_status("Invalid files", "")
        for file in invalid_files:
            error_msg = f"{file}: {results[file].error_message}"
            debug.log(_debug.DebugCategory.VALIDATION, error_msg)
            _console._print_status("", error_msg)

    return results
