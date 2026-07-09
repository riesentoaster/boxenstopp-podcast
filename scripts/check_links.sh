#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

command -v lychee >/dev/null || {
  echo "lychee not found; install with: brew install lychee" >&2
  exit 1
}

export JEKYLL_ENV=production

domain="$(grep '^url:' _config.yml | awk '{print $2}' | sed 's|https://||')"

if [[ "${1:-}" != "--skip-build" ]]; then
  bundle exec jekyll build
fi

# lychee only finds HTML <a href> in feed.xml, not enclosure/transcript/image URLs
feed="_site/feed.xml"
feed_links="_site/.feed-links.html"
{
  echo '<!DOCTYPE html><html><body>'
  {
    grep -oE '(url|href)="https://[^"]+"' "$feed" | sed 's/.*="//;s/"$//' || true
    grep -oE '<link>https://[^<]+</link>' "$feed" | sed 's/<link>//;s/<\/link>//' || true
    grep -oE '<url>https://[^<]+</url>' "$feed" | sed 's/<url>//;s/<\/url>//' || true
    grep -oE 'src="https://[^"]+"' "$feed" | sed 's/.*="//;s/"$//' || true
  } | sort -u | while read -r url; do
    printf '<a href="%s"></a>\n' "$url"
  done
  echo '</body></html>'
} > "$feed_links"

lychee --verbose --no-progress \
  --root-dir "$PWD/_site" \
  --remap "^https://${domain//./\\.} file://$PWD/_site" \
  "_site/**/*.html" "$feed_links"
