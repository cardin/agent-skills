#!/usr/bin/env bash
# Capture the Windows desktop and print the screenshot's WSL path.
#
# Usage: capture.sh [-m MONITOR] [-w MAXWIDTH] [-o OUTDIR]
#   -m N   0 = all monitors (default), 1..N = a single display
#   -w N   downscale so the image is at most N px wide (0 = full size)
#   -o DIR output directory (a Windows path, or a WSL path translated for you)
#
# Prints:  <wsl-path-to-png>
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PS1_WIN="$(wslpath -w "$SCRIPT_DIR/screenshot.ps1")"

MONITOR=0
MAXWIDTH=0
OUTDIR=""

while getopts ':m:w:o:' opt; do
	case "$opt" in
	m) MONITOR="$OPTARG" ;;
	w) MAXWIDTH="$OPTARG" ;;
	o) OUTDIR="$OPTARG" ;;
	*)
		echo "usage: capture.sh [-m MONITOR] [-w MAXWIDTH] [-o OUTDIR]" >&2
		exit 2
		;;
	esac
done

ps_args=(-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "$PS1_WIN"
	-Monitor "$MONITOR" -MaxWidth "$MAXWIDTH")
if [[ -n "$OUTDIR" ]]; then
	ps_args+=(-OutDir "$(wslpath -w "$OUTDIR")")
fi

out="$(powershell.exe "${ps_args[@]}")"

win_path="$(printf '%s\n' "$out" | sed -n 's/^PATH=//p' | tr -d '\r')"
if [[ -z "$win_path" ]]; then
	echo "screen capture failed:" >&2
	printf '%s\n' "$out" >&2
	exit 1
fi

wslpath -u "$win_path"
