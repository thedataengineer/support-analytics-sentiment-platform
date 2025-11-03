#!/usr/bin/env bash

# ------------------------------------------------------------------
#  find_and_replace_datepicker.sh
#
#  Replaces the old MUI slotProps usage with renderInput in all .js/.tsx files.
#
#  Usage:
#     ./find_and_replace_datepicker.sh   # run the replacement
#     ./find_and_replace_datepicker.sh -n  # dry‑run: only show what would change
# ------------------------------------------------------------------

set -euo pipefail

DRY_RUN=false
while getopts "n" opt; do
  case "$opt" in
    n) DRY_RUN=true ;;
    *) echo "Usage: $0 [-n]"; exit 1 ;;
  esac
done

# Pattern to search for (old API)
SEARCH='slotProps={[[:space:]]*textField:[[:space:]]*{[^}]*}}'
# Replacement (new API)
REPLACE='renderInput={(params) => <TextField {...params} size="small" />}'

# Find all .js and .tsx files that contain the search string
FILES=$(grep -rl --exclude-dir=node_modules --exclude=*.min.js "$SEARCH" src)

if [[ -z $FILES ]]; then
  echo "No matches found."
  exit 0
fi

echo "Found $FILES"
echo ""

for FILE in $FILES; do
  echo "=== $FILE ==="

  if $DRY_RUN; then
    # Show diff instead of editing
    echo "Dry run – what would change:"
    grep -n "$SEARCH" "$FILE"
  else
    # Make a backup first
    cp "$FILE" "${FILE}.bak"

    # Perform the in‑place replacement
    sed -i.bak "s|$SEARCH|$REPLACE|g" "$FILE"

    # Show what was changed (git diff style)
    git --no-pager diff --color=always "$FILE" "${FILE}.bak"

    # Clean up backup created by sed
    rm -f "${FILE}.bak"
  fi

  echo ""
done

echo "✅ Done."
