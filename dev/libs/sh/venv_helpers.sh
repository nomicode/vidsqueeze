
# shellcheck shell=sh
# shellcheck source=dev/lib/sh/exit_helpers.sh

# Source this file in your script; do NOT execute it directly!

get_repo_dir() {
    script_dir="$(dirname "${0}")"
    cd "${script_dir}" ||
        echo "Could not change to script directory" >&2 && exit 1

    # Use Git to determine the root project directory
    repo_dir="$(git rev-parse --show-toplevel)"
    if ! test -d "${repo_dir}"; then
        echo "Git repository directory not found" >&2
        exit 1
    fi
    echo "${repo_dir}"
}

venv_get_path() {
    repo_dir="$(get_repo_dir)"
    cd "${repo_dir}" || \
        echo "Could not change to repository directory" >&2 && exit 1

    if ! command -v poetry > /dev/null; then
        echo "Poetry not found" >&2
        exit 1
    fi

    # Use Poetry to get the virtual environment path
    poetry env info --path
}

venv_get_bin_path() {
    bin_name="${1}"
    bin_path="$(get_path)/bin/${bin_name}"

    if test ! -f "${bin_path}"; then
        echo "Binary not found: ${bin_path}" >&2
        exit 1
    fi

    if test ! -x "${bin_path}"; then
        echo "Binary not executable: ${bin_path}" >&2
        exit 1
    fi

    echo "${bin_path}"
}
