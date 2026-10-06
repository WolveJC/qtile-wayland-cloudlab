#!/usr/bin/env bash
# ~/.config/qtile/scripts/lib_log.sh

run_logged() {
    local log_file="$1"
    shift
    (
        echo "=== Sesión iniciada: $(date '+%Y-%m-%d %H:%M:%S') ==="
        "$@"
    ) >> "$log_file" 2>&1 &
}
