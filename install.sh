#!/usr/bin/env bash
set -euo pipefail

readonly repository="matt-byers/unit-loop-engineering"
temporary_directory=""

cleanup() {
  if [[ -n "$temporary_directory" ]]; then
    rm -rf "$temporary_directory"
  fi
}

trap cleanup EXIT

if [[ -n "${UNIT_LOOP_SOURCE_DIR:-}" ]]; then
  source_directory="$UNIT_LOOP_SOURCE_DIR"
else
  temporary_directory="$(mktemp -d)"
  archive="$temporary_directory/unit-loop-engineering.tar.gz"
  curl -fsSL "https://github.com/$repository/archive/refs/heads/main.tar.gz" -o "$archive"
  tar -xzf "$archive" -C "$temporary_directory"
  source_directory="$temporary_directory/unit-loop-engineering-main"
fi

for surface in skills agents hooks; do
  mkdir -p ".claude/$surface"
  rsync -a --ignore-existing "$source_directory/$surface/" ".claude/$surface/"
done

printf 'Installed unit-loop-engineering into %s/.claude\n' "$PWD"
printf 'Next: claude "/unit-loop-setup"\n'
