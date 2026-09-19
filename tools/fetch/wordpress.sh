#!/bin/sh
# Pull a WordPress site's REST API rather than its HTML.
#
# Nearly every WordPress site answers /wp-json/wp/v2/, and what comes back is the
# post as data: the title, the write-up, the date, and -- in media -- the file
# each attachment points at and which post it belongs to. That last field is the
# whole prize. It turns "match write-ups to audio" from a guess into a join, and
# a guess is the part of an import that goes silently wrong.
#
#   ./wordpress.sh https://example.invalid [output-directory]
#
# Leaves posts.json and media.json behind, and the audio under the host's own
# directory tree. Needs curl and jq.
#
# Sites that have closed the media endpoint answer 401 or 404 for media.json.
# That is a decision somebody made; the pages are still there, so mirror the site
# with site.sh and read the HTML. Some archives work around it by probing every
# attachment id in turn, which is thousands of requests to guess at what the site
# declined to list -- not something to do without a reason you would say out loud.
set -eu
[ $# -ge 1 ] || { echo "usage: $0 <site-url> [dir]" >&2; exit 2; }
site=${1%/}
dir=${2:-.}
mkdir -p "$dir"
cd "$dir"
UA=${FETCH_UA:-driftspace-mirror/1}

pages() {
  # The total is a response header, and a site that omits it still has one page.
  curl -sI -A "$UA" "$1&per_page=100&page=1" \
    | awk -F': ' 'tolower($1)=="x-wp-totalpages"{gsub("\r","",$2);print $2+0}' \
    | tail -n1
}

collect() {
  what=$1
  total=$(pages "$site/wp-json/wp/v2/$what?context=view")
  [ -n "${total:-}" ] && [ "$total" -gt 0 ] 2>/dev/null || total=1
  echo "fetching $what: $total page(s)"
  p=1
  while [ "$p" -le "$total" ]; do
    # ?page= must carry the page number. Writing it only into the filename and
    # asking for page one every time is a loop that never ends and an archive
    # that is one page repeated -- which looks exactly like success.
    curl -sS -A "$UA" "$site/wp-json/wp/v2/$what?per_page=100&page=$p" > "$what-$p.json"
    p=$((p + 1))
    sleep 1
  done
  jq -s 'add // []' "$what"-*.json > "$what.json"
  rm -f "$what"-*.json
  echo "  $(jq 'length' < "$what.json") $what"
}

collect posts
collect media || echo "media endpoint unavailable; mirror the HTML with site.sh instead"

if [ -s media.json ]; then
  echo "fetching audio"
  jq -r '.[] | select((.mime_type // "") | startswith("audio")) | .source_url' < media.json \
    | wget --continue --force-directories --wait=1 --random-wait \
           --tries=3 --timeout=30 --user-agent="$UA" -i -
fi
