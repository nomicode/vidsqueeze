# shellcheck shell=sh
# shellcheck source=dev/lib/sh/exit_helpers.sh

# Source this file in your script; do NOT execute it directly!

# Exit successfully
exit_success() {
    exit 0
}

# Exit with error
exit_error() {
    exit 1
}

# Trap signals for clean exit
trap exit_success EXIT
trap exit_error HUP INT QUIT TERM
