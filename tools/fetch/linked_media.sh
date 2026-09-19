#!/bin/sh
# Mirror a site that serves one page per recording, then take what those pages
# point at.
#
# Some hosts put the audio on a separate domain and name it by hash, so a mirror
# of the site alone gets you every write-up and no audio, and a mirror of the
# media domain gets you a folder of hashes nobody can identify. You want both,
# and you want them from the same run -- the page is the only thing that knows
# what its file is called.
#
#   ./linked_media.sh https://example.invalid/u/somebody 'https://media\.example\.invalid/[^"'"'"' <]+'
#
# The second argument is the pattern the pages use for their audio. Quote it.
set -eu
[ $# -ge 2 ] || { echo "usage: $0 <url> <media-url-regex> [dir]" >&2; exit 2; }
url=$1
pattern=$2
dir=${3:-.}
UA=${FETCH_UA:-driftspace-mirror/1}
mkdir -p "$dir"
cd "$dir"

wget --recursive --no-parent --continue --page-requisites \
     --wait=1 --random-wait --tries=3 --timeout=30 --user-agent="$UA" "$url"

# Every media URL any mirrored page mentions, deduplicated. Fetched with
# --force-directories so the files land under their own host, which keeps the
# pages and the audio distinguishable afterwards.
find . -type f -print0 \
  | xargs -0 grep -hoE "$pattern" \
  | sort -u \
  | wget --continue --force-directories --wait=1 --random-wait \
         --tries=3 --timeout=30 --user-agent="$UA" -i -
