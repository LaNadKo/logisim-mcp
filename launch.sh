#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
case "$(uname -s)" in Linux) OS=linux;; Darwin) OS=macos;; *) echo 'Supported: Linux and macOS. On Windows use launch.cmd.' >&2; exit 1;; esac
case "$(uname -m)" in x86_64) ARCH=x64;; aarch64|arm64) ARCH=arm64;; *) echo 'Unsupported CPU architecture.' >&2; exit 1;; esac
KEY="$OS-$ARCH"
RUNTIME="$ROOT/.runtime/$KEY"
mkdir -p "$RUNTIME"
umask 077
ATTEMPT=0
until mkdir "$RUNTIME/bootstrap.lockdir" 2>/dev/null; do
    ATTEMPT=$((ATTEMPT + 1))
    if [ "$ATTEMPT" -ge 60 ]; then echo 'Another extraction is running, or a stale bootstrap.lockdir remains after interruption.' >&2; exit 1; fi
    sleep 1
done
trap 'rmdir "$RUNTIME/bootstrap.lockdir"' EXIT
trap 'exit 1' HUP INT TERM
# Manifest is generated from the pinned JSON lock, with relative filenames and SHA-256 only.
while IFS=' ' read -r HASH REL; do
    case "$REL" in "runtime-archives/$KEY/"*) ;; *) continue;; esac
    case "$REL" in *cpython*) KIND=python;; *OpenJDK*) KIND=java;; *) exit 1;; esac
    DEST="$RUNTIME/$KIND"
    if [ -f "$DEST/.archive-sha256" ] && [ "$(cat "$DEST/.archive-sha256")" = "$HASH" ]; then continue; fi
    ARCHIVE="$ROOT/$REL"
    if [ ! -f "$ARCHIVE" ]; then echo "Runtime missing: $REL. Use the universal portable release or scripts/fetch_dependencies.py." >&2; exit 1; fi
    if command -v sha256sum >/dev/null 2>&1; then ACTUAL=$(sha256sum "$ARCHIVE" | cut -d ' ' -f 1); else ACTUAL=$(shasum -a 256 "$ARCHIVE" | cut -d ' ' -f 1); fi
    if [ "$ACTUAL" != "$HASH" ]; then echo "Checksum mismatch: $REL" >&2; exit 1; fi
    echo "Preparing bundled $KIND; this happens once per platform..." >&2
    STAGE=$(mktemp -d "$RUNTIME/.extract-$KIND.XXXXXX")
    tar -xzf "$ARCHIVE" -C "$STAGE"
    printf '%s' "$HASH" > "$STAGE/.archive-sha256"
    if [ -d "$DEST" ]; then mv "$DEST" "$DEST.previous.$$"; fi
    mv "$STAGE" "$DEST"
done < "$ROOT/runtime-archives/SHA256SUMS"
PYTHON="$RUNTIME/python/python/bin/python3"
if [ ! -x "$PYTHON" ]; then echo 'Bundled Python executable missing. Check archive and executable permissions.' >&2; exit 1; fi
rmdir "$RUNTIME/bootstrap.lockdir"
trap - EXIT HUP INT TERM
exec "$PYTHON" -I -X utf8 "$ROOT/launcher.py" "$@"
