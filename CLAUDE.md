# Working notes for an agent

This is a Driftspace library: a working directory where
[Inductor](https://github.com/NaomiAmethyst/inductor) turns audio into YAML and
[Hypnotica](https://github.com/NaomiAmethyst/hypnotica) turns that YAML into a
website. You are here to get somebody's collection of spoken-audio recordings
into it.

Read this file first. Each directory has its own `README.md` with the detail for
that directory; this one covers the shape of the job and the traps.

Three pieces, and keeping them separate is the point:

| | |
|---|---|
| `content/` | the library itself: YAML, and the only thing that matters long-term |
| Hypnotica | turns `content/` into a website. Knows nothing about where it came from |
| Inductor | fills `content/` from audio. Knows nothing about websites |

Both tools are public repositories of their own. **Nothing you write here should
end up needing a change in either of them**, and nothing you write in a parser
here should assume anything about another source.

## This directory belongs to whoever cloned it

It is a starting point, not a specification. Most of what ships here exists so
that the first hour is spent importing recordings rather than deciding where
things go — and it is meant to be changed once the shape of a particular library
is clear. Two kinds of thing are mixed together in these notes, and it is worth
knowing which is which.

**Yours to change, and expected to change:**

- **`content/tags.yaml`** above all. It ships as a starting vocabulary, not a
  finished one: the tags a library actually needs are the ones its recordings
  turn out to be about. Expect to add, rename, merge and re-file entries as they
  accumulate, and use `inductor registry` for it so the items, the creator maps
  and the ruling ledger move with the registry rather than drifting from it. A
  vocabulary nobody edits does not stay tidy — it accretes. One library reached
  843 entries carrying lower-case leftovers, symbol prefixes, three spellings of
  "toys" and a dozen tags filed in the wrong namespace, every one of them
  arriving one reasonable-looking decision at a time.
- **These notes, and each directory's `README.md`.** Write down what this
  library learns. A note that has drifted from what the library actually does is
  worse than no note, because it is believed.
- **`tools/mirrors/example_wordpress.py`** — a worked example to copy or delete.

**Load-bearing, and not arbitrary:**

- The three pieces staying separate, and `content/` being the thing that
  matters. Everything else can be rebuilt from it; it cannot be rebuilt from
  anything else.
- `content/` permanent, `state/` expensive, `cache/` disposable.
- A tag reaching an item only through the registry.
- Changing the library through commands rather than by hand-editing YAML.

The reasons for those four are written down further on, each with what it cost
to learn. Change them if the reasons stop applying — but read the reason first.

**The namespaces are yours too, and they live in `content/tags.yaml`.**
`Voice:`, `Audience:`, `Induction:`, `Production:`, `Trigger:`, `Compulsion:`,
`CW:` and the unprefixed content namespace are what a registry gets when it says
nothing — they are a claim about what is worth separating in *these* recordings,
and a library of guided meditations or audio drama may want different ones.
Declare them and both tools follow:

```yaml
apiVersion: hypnotica/v1
kind: Tags
namespaces:
  - key: setting
    prefix: Setting
    label: Settings
    note: where it takes place
    colour: '#445566'
    dark: '#99aabb'
  - key: warning
    prefix: Warning
    label: Warnings
    spoiler: true
  - key: subject          # no prefix: where bare tags go
    label: Subject
setting:
  Forest: Among trees.
```

The order is the order sections appear. `spoiler` puts a section behind the
spoiler control, as triggers and compulsions are. `colour` becomes that
namespace's chip colour, and a namespace without one reads as ordinary text
rather than as broken. Inductor files tags by the same list, so
`inductor registry add "Setting: Cave"` lands in the right block and
`"Voice: fem"` is refused when no `Voice` namespace is declared.

Adding a block *without* declaring it is the quiet failure: an unrecognised
prefix is filed under the unprefixed namespace and renders as an ordinary tag,
so the tags resolve, nothing errors, and the section simply never appears.

## Before you start

Check that the tools are there and the library validates:

```sh
inductor --version && hypnotica --help && ffmpeg -version | head -1
inductor check && hypnotica -s content check
```

Then find out what you are working with. The answers change the whole route, and
guessing at them wastes a run:

- **Where is the audio, and is it writable?** Archives are often read-only
  mounts. Nothing generated may be written beside them.
- **What else came with it?** A site mirror, a pack README, a spreadsheet, ID3
  tags, nothing at all. This decides whether you write a parser or start from
  `inductor add`.
- **One creator or many?** `sources/` is one file per creator, and a folder of
  mixed material has to be split before it can be a source record.
- **Is there a GPU for transcription, and an OpenRouter key?** Without them you
  can still import, tag and build; you cannot transcribe or write entries.

Ask. Do not infer a creator's name from a folder name and commit to it — ids are
permanent once items reference them.

## The pipeline

```
  a site mirror, a folder of mp3s, a pack with a README
        │
        │  a parser you write for that one source        tools/mirrors/
        ▼
  sources/<creator>.yaml     kind: Source — audio, title, author, whatever else
        │
        │  inductor run                                  transcode · transcribe
        ▼                                                measure · enrich · tag
  content/<creator>/*.yaml   kind: Item, Author, Transcript
        │
        │  hypnotica build
        ▼
  www/
```

Each arrow is re-runnable and cached. Nothing later in the chain reaches back:
Hypnotica never transcribes, Inductor never renders.

## Ingesting new material

### 1. Get it into source records

A source record is what some parser managed to learn about one recording. Only
`audio`, `title` and `author` are required.

```yaml
apiVersion: inductor/v1
kind: Source
audio: /path/to/Some Recording.m4a
title: Some Recording
author: Some Creator
date: 2025-11-18
description: |
  <p>Whatever the site said.</p>
tags: [Femdom, Hypnosis]        # their words, mapped later — do not clean them
source_url: https://example.com/some-recording/
```

For a plain folder of audio with nothing else, skip the parser:

```sh
inductor add ~/audio/some-creator/*.mp3 --author-name "Some Creator" --dry-run
```

**Leave the source's tags exactly as the source spelled them.** Mapping them onto
the registry is a later, separate step that a model does per creator. Cleaning
them here loses the evidence of what they actually said.

### 2. Write the parser in `tools/mirrors/`

One file per source, named after it. They are disposable by design: the source
record is the stable interface, the parser is not. Write it, run it, keep it for
when the site changes. See [`tools/mirrors/README.md`](tools/mirrors/README.md).

Before writing one, **find the data seam** — it is rarely the rendered HTML:

| platform | where the data actually is |
|---|---|
| WordPress | `posts*.json`, or per-post `index.html` under date paths |
| WooCommerce | `/product/<slug>/index.html` |
| VirtueMart | `*-detail.html`, description in `.product-description` |
| MediaWiki | article pages; tracklist tables |
| JS-paginated shop | **the captured AJAX responses**, not the HTML |
| Next.js | `__NEXT_DATA__` |
| Bandcamp / Gumroad | the embedded JSON blob in the page `<script>` |
| A pack README | one block per track; write the block splitter first |

### 3. Check before you trust

```sh
inductor check
```

Parsers fail by producing well-formed YAML about the wrong data, which looks
exactly like success. The checks that have actually caught this:

- **The same audio claimed twice.** One mirror's fifteen paginated files all held
  page one; the parser dutifully emitted the same recording fifteen times.
- **A match rate that is obviously wrong.** A mirror with 117 posts matched zero
  files, because the site had become a different site since the archive was made.
- **Counts against what the source claims.** If a shop says 971 products and you
  have 35, you found the listing page, not the catalogue.

Two minutes grepping a mirror for a few known titles saves an hour.

### 4. Ingest

```sh
inductor tagmap --author some-creator        # map their vocabulary onto the registry
inductor run --author some-creator           # media, transcribe, analyse, review, emit
inductor adjudicate                          # rule on any tag the run wants to add
inductor adjudicate --apply --write          # after reading the rulings
inductor duplicates                          # anything imported twice
inductor orphans                             # creator pages and transcripts nothing refers to
hypnotica -s content build -o www --media link
```

`run` is a dependency-graph dispatcher, not a loop over stages: it works out
what each recording is still missing and schedules it across lanes — `disk`,
`cpu`, `gpu`, `api`, `batch`, `art` — so transcription on the GPU overlaps with
measurement, analysis and the batched review rather than waiting its turn. It
also builds three artefacts that `ingest --stage` has no name for at all:
`measurements`, `voiceprint` and `cover`.

So `run` is the one to reach for, including when you are being careful. Going
stage by stage to keep a close eye on an import buys nothing: it is slower, and
it leaves the items short of artefacts you would then have to notice were
missing. `ingest --stage` is for wanting *less* than the graph on purpose —
`media`, `transcribe`, `analyse`, `review`, `emit`, any subset, as when you are
keeping transcripts away from a model provider. `--needs spoilers` narrows
either to the items still missing something. Three flags worth knowing:

- **`--overwrite` is what lets a run replace a summary or spoilers that already
  exist.** Without it nothing already written is touched, which is what makes a
  re-run safe to point at the whole library. The default is not timidity: a
  version of the item writer that rebuilt each item from its source record lost
  the summary and spoilers of 381 live items in one run.
- **`--recover <batch-id>`** adopts a review batch that was already submitted. A
  killed process does not cancel one, and there is no cancel endpoint.
- **`--no-covers`** skips artwork, which needs a running ComfyUI. Covers are off
  in the shipped config; turn them on when you have one.

Two caches make a re-run cheap, both keyed on what the filesystem already knows:
a fingerprint index (device and inode, checked against size and mtime) and an
item index (size and mtime per item file), both under `cache/inductor/`. Delete
either one and the next run is merely slow.

## Resolving ambiguity

When a file's name cannot be trusted, escalate in this order and stop at the
first confident answer. Each is stronger than the ones below it.

1. **Audio fingerprint** against the library — immune to renaming and re-tagging,
   and free, so always first. It answers "we already have this" and never "we do
   not": a shop that serves a separate copy per *listing* can give one
   performance a dozen different fingerprints, differing by a few dozen bytes in
   a 58 MB payload, and pass the same-audio-twice check clean.
2. **Acoustic fingerprint** — finds the same recording at a different bitrate,
   and finds *where* a preview sits inside a full recording. `inductor acoustic`,
   then `inductor acoustic-apply`. This is the strongest identification
   available. Its cheap end is a **loudness envelope**, one figure per second
   over a few minutes: two encodes of one performance correlate at 1.0000 and two
   different recordings of the same length do not come close. It costs one short
   decode a side, needs nothing but FFmpeg, and is what a parser can afford to
   run over a whole mirror.
3. **A preview found inside the recording.** If a site names previews after the
   post slug, the slug hands over the real title.
4. **ID3.** Date, album and artist survive when titles do not.
5. **Rare-vocabulary matching** between a write-up and a transcript.
6. **A curated gap list** — cross-check date *and* duration band.
7. **An LLM title from the transcript** — last resort, and only for material that
   was never published. Asked to name a file the site already called "Going
   Primal", a model invented "Regression to the Primal Self", and both ended up
   in the library.

**When signals conflict:** duration beats everything for release-versus-preview;
require a *margin* over the runner-up, not just a best score; assign one-to-one;
a proposed id ending `-2` is a warning, not a resolution; and prefer no metadata
to wrong metadata, because `needs:` gets filled in later and a wrong description
is silent and permanent.

## Conventions

- **Every document declares itself**: `apiVersion: hypnotica/v1` and
  `kind: Item | Author | Transcript | Config | Tags`. Never infer a document's
  type from its path — that assumption has broken four separate times.
- **Item ids are global in Hypnotica**, so they carry the creator
  (`some-creator-asmr-tease`). Filenames come from the title; ids do not change.
- **`needs:`** lists what an item is still missing. The pipeline selects on it.
- **`provenance:`** records where metadata came from, and what this toolchain
  generated versus what arrived with the item. Never drop it.
- **Tags** come from `content/tags.yaml` — the registry, and *only* from there.
  A tag that is not in it never reaches an item: it is recorded in
  `provenance.proposed_tags` and put to the pipeline — `inductor tagmap` for a
  creator's vocabulary, `inductor adjudicate` for what a run proposes. This
  applies to a creator's own tags too. Letting unruled tags sit on items is how
  874 unregistered spellings accumulated across 558 of them in one library.
- **The registry wins, always.** A creator's map exists to say what their
  vocabulary becomes *in the registry*, so a row's `to:` may only name a tag the
  registry already has. A row pointing anywhere else is not an answer and never
  outranks the registry: the tag resolves as written, `inductor check` reports
  the row under `map_targets_missing`, and the row is to be adjudicated into the
  registry or dropped from the map. A target a `tagmap` run wants but the
  registry lacks is therefore not written as a mapping at all — it goes to
  `pending:` in the same file, which `inductor adjudicate` reads, and only a
  ruling can promote it.

  This is the trap that looks most like success. A row reads as settled, so
  nothing flags it, and the tag it was meant to place quietly stops resolving.
  In one library 100 such rows across five creators pointed at plausible names —
  `Humour`, `Exercise`, `Strong Woman` — that nobody ever added, and because a
  map used to outrank the registry, a single `retag` stripped 1,029 registered
  tags off 675 recordings. Every one was a tag the registry already had, under
  the spelling the item was using.
- **`Audience: sissy` is not `Audience: transfem`.** One is a kink about being
  made into a woman; the other is a woman. A registry that said transfem covered
  "feminisation framed as such" filed 343 recordings that call the listener a
  feminised male under a trans audience — where a trans woman browsing for
  herself found them. Split on evidence: the sissy vocabulary in the transcript
  and the sissy content tags against transition language and the creators' own
  `tg m→f` tagging.
- **`CW:`** is for what a recording *touches on*; a bare content tag is for what
  it is *about*. Snuff is content because killing is the draw; `CW: Death` is a
  warning because somebody dies in the story.
- **`video:`** is the container a recording arrived in, kept beside the `audio:`
  extracted from it. Only the item page shows it; the player, the queue and
  anything saved offline take the audio track.
- **Paths are written relative** where they point inside the library —
  `../../media/cover/<creator>/<id>.png` from an item, `media/audio/...` for a
  source key — so the whole directory can be moved or cloned. Anything outside
  it, a read-only archive mount above all, stays absolute. `inductor paths
  --write` normalises a tree that predates this.
- **`provenance.generated:`** lists, by field name, what this toolchain wrote
  rather than found — `[cover, spoilers, summary]`. The site marks those lines
  and leaves the rest alone. Nothing is inferred from how a value reads: an
  entry that does not say is left unmarked, because telling somebody their own
  writing was machine-made is the one error worth ruling out. `inductor
  attribute` fills it in for entries that predate it.
- **`cover_prompts:`** holds the image prompt in both styles — `tagged` for
  SDXL-family renderers, `natural` for Flux/SD3-family ones — so changing
  renderer is a flag, not another pass over the library.

## Things that have already cost time

**Filenames lie, in both directions.** Deliberate noise (`Bl00d3y_r3l34s3_FINAL2`), a
`-Custom` suffix that does not mean a custom, `Mixdown` copies beside titled
ones. In one library 112 recordings were claimed by two items each;
`inductor duplicates` sorts them, folds the ones that differ only by a numeric
suffix, and leaves the ones that disagree about the *title* for a person, because
that disagreement is not resolvable from the data.

**A page is a listing, not a recording.** A catalogue row and a performance are
different things, and a site that sells variants — the same audio listed as
male-dom and female-dom, with and without an orgasm — has more rows than it has
recordings. One shop had 1,184 rows over 1,085 recordings, and eleven rows
sharing a title disagreed about what they did while pointing at one performance.
Where a group like that disagrees about a field, at most one row is describing
the audio, so the field is dropped rather than picked from.

**Preview clips are the main contamination risk.** They run a flat 60 or 110
seconds. Only duration reliably tells a teaser from a release; a name-based
filter once proposed 140 previews as new releases.

**Check ID3 before generating anything** — but never read the genre byte as a
tag. Twenty-eight unrelated creators did not each decide their hypnosis was
"Blues"; that byte put 770 junk tags into one library.

**An unquoted numeric tag name makes its whole registry block invisible.**
`69:` and `360:` parse as integer keys, so `content:` and `production:` decode as
a non-string map, Inductor's type assertion fails, and it reads those blocks as
*empty* — every tag in them silently stops resolving, and `adjudicate --apply
--write` then rewrites the block containing only the tag it just added. Nothing
errors. Quote them: `'69'`. After editing `content/tags.yaml`, check it by
ingesting a source record tagged with something you know is registered and
confirming it lands in `tags:` rather than `provenance.proposed_tags`.

**Whisper mishears creator names.** That leaks into generated titles, summaries
and spoilers. Normalise them.

**Treat the source archive as read-only** whether or not it is mounted that way.
Anything generated goes inside this directory.

**A cache that is not there reports every recording as untranscribed.** Tools
have resolved paths that had stopped existing and raised nothing: `rglob` on a
missing directory returns nothing, and a missing author file just means a name
never gets filled in. One enrichment run sent the model `some-creator` instead of
`Some Creator` for every item, and nothing said so. Ask by declared id, and when
a scan returns zero, check the directory before believing it.

**A `--dry-run` that calls models still spends money.** It means "write nothing",
not "do nothing": it analyses and submits the review batch. And a killed process
does not cancel a submitted batch — adopt it with `--recover <batch-id>` rather
than paying for the same reviews twice.

**`pgrep -f` matches the command line running it**, and `pkill -f <pattern>` in a
command containing the pattern kills its own shell. Bracket it: `[p]attern`.

## What not to do

- **Snapshot `content/` before any command that writes across the library** —
  a bulk retag, a duplicate fold, a registry change, an `adjudicate --apply`.
  `tar czf` of a few thousand YAML files takes seconds, and it is the difference
  between a ten-minute correction and a loss. It is also what makes a change
  checkable: diffing the result against the snapshot is the only way to find out
  what a command *actually* did, as against what it reported. Three separate
  mistakes in one session of this library were recoverable for that reason and
  no other.
- **Do not edit files under `content/` by hand to fix a systematic problem.**
  There is an Inductor command for it — `retag`, `fold`, `retitle`, `paths`,
  `attribute`, `authors` — and hand edits across hundreds of files do not leave
  a record of what was decided.
- **Do not add a tag to an item that is not in `content/tags.yaml`.** Propose it
  and let `adjudicate` rule. Where a person has decided directly, the command is
  `inductor registry add|describe|remove|rename|merge`, or `registry bulk` for a
  file of changes — never an edit to `content/tags.yaml` on its own, which moves
  one of the five places a tag is written down and leaves the other four
  disagreeing silently. See
  [`state/decisions/README.md`](state/decisions/README.md).
- **Do not delete anything under `state/`.** Transcripts are GPU-hours and
  rulings are judgements nobody can reconstruct. `cache/` is the disposable one.
- **Do not put the user's material, paths, or creators' names into anything
  destined for the Hypnotica or Inductor repositories.**
- **Do not commit the audio.** See the note on `media/` in the root README.
- **Do not publish.** `base_url` stays on localhost and `www/` stays local
  unless the user says otherwise; this is somebody's private collection.
