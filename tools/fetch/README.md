# tools/fetch/ — getting the mirror in the first place

The pipeline starts at "a site mirror, a folder of mp3s, a pack with a README".
These are for the first of those. A parser in `tools/mirrors/` turns a mirror
into source records; nothing turns a website into a mirror, so this is that.

They are deliberately small and deliberately generic. Copy one and change it the
moment a site wants something different — like the parsers, a fetcher is
disposable and the thing it produces is the interface.

| script | for |
|---|---|
| `site.sh` | any site. Mirrors the pages and stops there |
| `wordpress.sh` | WordPress, through its REST API rather than its HTML |
| `linked_media.sh` | sites that serve one page per recording with the audio on another host |

## Take the seam, not the page

`site.sh` is the fallback, not the default. Before reaching for it, look for the
machine-readable version of the same thing — `tools/mirrors/README.md` has the
table of where each platform keeps it. Parsing rendered HTML works until the
theme changes; parsing what the site's own front end reads keeps working.

WordPress is worth the special case because its media endpoint records **which
post each attachment belongs to**. With that, matching write-ups to audio is a
dictionary lookup. Without it you are guessing from titles, and a title is
exactly what a preview, a looping edit and the release all have in common.

## Two failures that look like success

**A paginated fetch that never advances.** Put the page number in the *request*,
not only in the output filename. A loop that writes `page-1`, `page-2`, `page-3`
from the same URL produces an archive that is one page repeated — and, if the
API's "is there more?" flag keeps saying yes, a loop that never ends. Both of
those look fine in the output directory. Check that page two differs from page
one before you trust a paginated anything.

**A mirror that stopped early.** Nothing announces this. `wget` exits zero having
fetched half a site, a rate limit having quietly started returning errors it
retried past. Count what you got against what the site claims — a shop that says
971 products and a mirror with 35 means you found the listing page, not the
catalogue. `inductor check` makes the same comparison from the other end.

## Etiquette, and why it is also self-interest

Every script here waits between requests and identifies itself. That is not
decoration:

- A mirror taken at full speed gets rate-limited partway through, and what you
  end up with is an archive missing its second half *without saying so*. Slow is
  the difference between a complete mirror and one you cannot tell is broken.
- `--continue` everywhere, so an interrupted run resumes rather than restarting.
- Set `FETCH_UA` to something that says who you are and how to reach you if a
  site operator would rather you did not.

Fetch what you are entitled to fetch. A closed endpoint is somebody's decision:
WordPress sites that answer 401 for `media` have turned it off, and probing every
attachment id in turn to get the list anyway is thousands of requests to work
around an answer you were already given. If the pages are public, mirror the
pages.

## Afterwards

A fetcher's job ends with bytes on disk. What those bytes *mean* is
`tools/mirrors/` — and `example_wordpress.py` and `example_soundgasm.py` are the
two shapes you will meet: one where the write-ups and the audio have to be
married by inference, and one where the page names its own file and there is
nothing to infer.
