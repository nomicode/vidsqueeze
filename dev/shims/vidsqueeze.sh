# #!/bin/sh -e

# Get script directory
script_dir="$(dirname "${0}")"

. "${script_dir}/../lib/dev_script_helpers.sh"

exec_bin "$@"

# # Project command name
# BIN_NAME=vidsqueeze

# # Get script directory
# script_dir="$(dirname "${0}")"

# get_repo_dir() {
#     cd "${script_dir}"
#     # Use git to get the root of the repository
#     repo_dir="$(git rev-parse --show-toplevel)"
# }

# get_path() {
#     repo_dir="$(get_repo_dir)"
#     cd "${repo_dir}"
#     # Use Poetry to get the virtual environment path
#     poetry env info --path
# }

# bin_name(){
#     env_path="$(get_path)"
#     echo "${env_path}/bin/${BIN_NAME}"
# }

# test_bin(){
#     bin_file="$(bin_name)"
#     if test ! -f "${bin_file}"; then
#         echo "Binary not found: ${bin_file}" >&2
#         exit 1
#     fi
# }

# exec_bin(){
#     bin_file="$(bin_name)"
#     # Replace the current process with the Python process
#     exec "${bin_file}" "$@"
# }

# exec_bin "$@"
