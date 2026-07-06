#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

command -v lychee >/dev/null || {
  echo "lychee not found; install with: brew install lychee" >&2
  exit 1
}

export JEKYLL_ENV=production

domain="$(grep '^url:' _config.yml | awk '{print $2}' | sed 's|https://||')"

bundle exec jekyll build
lychee --verbose --no-progress \
  --root-dir "$PWD/_site" \
  --remap "^https://${domain//./\\.} file://$PWD/_site" \
  "_site/**/*.html"
