import asyncio
import os
import pathlib

from . import _ffmpeg, _pbar


async def process_file(
    input_file,
    output_suffix,
    no_audio,
    resolution,
    fps,
    lossless,
    quality,
    verbose,
    very_verbose,
):
    # Split the input file path into its base name and extension
    base, ext = pathlib.Path(input_file).stem, pathlib.Path(input_file).suffix
    output_file = f"{base}{output_suffix}.{ext}"
    await _ffmpeg._compress_video(
        input_file,
        output_file,
        no_audio,
        resolution,
        fps,
        lossless,
        quality,
        verbose,
        very_verbose,
    )


async def compress_file(
    semaphore,
    input_file,
    output_suffix,
    no_audio,
    resolution,
    fps,
    lossless,
    quality,
    verbose,
    very_verbose,
):
    async with semaphore:
        try:
            await process_file(
                input_file,
                output_suffix,
                no_audio,
                resolution,
                fps,
                lossless,
                quality,
                verbose,
                very_verbose,
            )
        except Exception as e:
            print(f"Error processing file {input_file}: {str(e)}")


def process_files(
    input_files, no_audio, resolution, fps, lossless, quality, verbose, very_verbose
):
    suffix_parts = ["ffmpeg"]
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

    async def main():
        # Determine the number of CPU cores and use it to set the maximum number of concurrent tasks
        max_workers = os.cpu_count() or 1
        semaphore = asyncio.Semaphore(max_workers)

        # Initialize the MultiFileProgressBar
        total_size = sum(os.path.getsize(file) for file in input_files)
        _pbar.init_multi_file_pbar(len(input_files), total_size)

        tasks = [
            compress_file(
                semaphore,
                input_file,
                output_suffix,
                no_audio,
                resolution,
                fps,
                lossless,
                quality,
                verbose,
                very_verbose,
            )
            for input_file in input_files
        ]
        await asyncio.gather(*tasks)

        # Close the progress bar
        _pbar.close_pbar()

    asyncio.run(main())
