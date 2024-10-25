# shellcheck shell=sh
# shellcheck source=dev/lib/sh/exit_helpers.sh

# Source this file in your script; do NOT execute it directly!

# Print "Error:" in bold red followed by the message in white, output to STDERR
print_error() {
    printf "\033[1;31mError:\033[0m %s\n" "$1" >&2
}

# Print an error message and exit with status code 1
exit_error() {
    print_error "$1"
    exit 1
}
