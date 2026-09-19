#!/bin/sh
# Mirror a site, resumably.
#
# The plainest fetcher there is, and the right one when a site has no
# machine-readable seam: take the pages, work out what they mean later. Every
# other script here exists because some site offered something better.
#
#   ./site.sh https://example.invalid/ [output-directory]
#
# -m mirrors, -np stays under the starting path, -c resumes a part-done run, and
# --wait spaces the requests out. The wait is not optional politeness: a mirror
# taken at full speed is how you get blocked halfway through and end up with an
# archive that is missing its second half without saying so.
set -eu
[ $# -ge 1 ] || { echo "usage: $0 <url> [dir]" >&2; exit 2; }
url=$1
dir=${2:-.}
mkdir -p "$dir"
cd "$dir"
exec wget --mirror --no-parent --continue \
     --wait=1 --random-wait --tries=3 --timeout=30 \
     --adjust-extension --page-requisites \
     --user-agent="${FETCH_UA:-driftspace-mirror/1}" \
     "$url"
