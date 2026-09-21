# tools/mirrors/ — one parser per source

A parser is what turns "a mirror of somebody's site" into `sources/<creator>.yaml`.
One file per source, named after it.

**They are disposable by design.** The source record is the stable interface; the
parser is not. Write it, run it, keep it for when the site changes. Do not try to
make one parser handle two sites — the second site will be different in a way
that quietly breaks the first.

Three worked ones. The first two are the two shapes you will meet when the
thing you are importing is a recording:

- [`example_wordpress.py`](example_wordpress.py) — a WordPress mirror plus a
  folder of audio in, a source file out. The write-ups and the audio arrive as
  separate piles and have to be married by inference, which is most of its
  length and all of its risk.
- [`example_soundgasm.py`](example_soundgasm.py) — a host that serves one page
  per recording, where the page names its own audio file. The join is a
  dictionary lookup and there is nothing to infer. Read it for what a source
  looks like when it hands you the answer, and for what it still withholds: no
  dates, and filenames that are hashes.

The third is about the people rather than the recordings:

- [`example_author_pages.py`](example_author_pages.py) — the same mirror, read
  for the creator's own bio, photograph and links, emitted as `kind: Author`
  records. Without it a creator page carries a synopsis a model wrote and an
  avatar a renderer drew while their own words sit unread in the mirror. Read
  it mostly for what it refuses: a picture from anybody else's domain, a
  login wall that extracts like prose, and a homepage, which is a shop window
  and not a biography.

Copy whichever is closer and change it, or read them for the shape and write
your own. `tools/fetch/` is what produces the mirror in the first place.

## 1. Find the data seam

It is rarely the rendered HTML. Look for the machine-readable thing first:

| platform | where the data actually is |
|---|---|
| WordPress | `posts*.json`, or per-post `index.html` under date paths |
| WooCommerce | `/product/<slug>/index.html` |
| VirtueMart | `*-detail.html`, description in `.product-description` |
| MediaWiki | article pages; tracklist tables |
| JS-paginated shop | **the captured AJAX responses**, not the HTML |
| Next.js | `__NEXT_DATA__` in a `<script>` |
| Bandcamp, Gumroad | an embedded JSON blob in a `<script>` |
| A pack README | one block per track; write the block splitter first |
| A siterip with no site | ID3, and then the transcript |

A few minutes with `find`, `grep -rl`, and `head` over the mirror is the whole of
this step:

```sh
find ~/mirrors/some-creator -name '*.json' | head
grep -rl '__NEXT_DATA__' ~/mirrors/some-creator | head -3
grep -rli 'a title you know is there' ~/mirrors/some-creator | head
```

That last one is the important one. If a title you know exists does not turn up,
the mirror does not contain what you think it contains, and no parser will fix
that.

## 2. Match posts to audio

This is where parsers actually go wrong. A post and an audio file are matched by
normalised title, and neither side is reliable: rips truncate names, sites use
SEO strings as titles, and the same recording is sold under three names.

The example does exact match, then a prefix pass for truncated names, then a
close-match pass. When that is not enough, the ladder in
[`CLAUDE.md`](../../CLAUDE.md#resolving-ambiguity) goes further — duration bands,
ID3, acoustic envelopes, rare-vocabulary matching against transcripts.

**Assign one-to-one, and require a margin over the runner-up rather than just a
best score.** Two files matching one post means the parser has made something up
about at least one of them.

## 3. Report, then check

A parser should print what it did, and the numbers should be read rather than
glanced at:

```
418 posts with a body
392 audio files, 388 matched, 4 not
    Some Truncated Nam
    ...
```

Then:

```sh
inductor check
```

Parsers fail by producing well-formed YAML about the wrong data, which looks
exactly like success. Three failures worth knowing about, all of them real:

- **The same audio claimed twice.** A mirror's fifteen paginated files all held
  page one; the parser dutifully emitted the same recording fifteen times.
- **A match rate that is obviously wrong.** 117 posts matched zero files, because
  the site had become a different site since the archive was made.
- **Counts against what the source claims.** A shop that says 971 products and a
  source file with 35 records means you found the listing page, not the
  catalogue.

## 4. Leave the tags alone

Whatever the site called its tags, write them down as the site spelled them.
Mapping them onto `content/tags.yaml` is a later, separate step that `inductor
tagmap` does per creator, and it needs the evidence.

The same goes for descriptions: keep the creator's own words. A parser that
"tidies" a write-up has destroyed the one piece of metadata the pipeline cannot
regenerate, because it was never derivable from the audio in the first place.

## A note on mirroring

Making the mirror is not this directory's job, but if you need one:

```sh
wget --mirror --page-requisites --convert-links --no-parent \
     --wait=1 --random-wait https://example.com/
```

Be polite about it — one request at a time, with a delay. These are small sites
run by individuals, often paying for their own bandwidth.
