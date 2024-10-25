#!/bin/sh -e

script_dir="$(dirname $0)"

find . -type f ! -name '*-ffmpeg-*' -print0 | xargs -0  "${@}"
