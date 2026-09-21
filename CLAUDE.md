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
  a website, a folder of mp3s, a pack with a README
        │
        │  a fetcher, where there is a site to fetch     tools/fetch/
        ▼
  a mirror on disk
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

[`examples/`](examples/) has one recording in every one of those shapes at once —
the source record a parser left, the item it became, and the transcript. Reading
the first two side by side is the shortest description of what the middle arrow
does, and the item's `provenance.generated` is the shortest description of what
it is honest about.

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

A sources file may also carry one `kind: Author` document — the creator's own
bio, picture and links, which a site mirror has and which are otherwise thrown
away and then reinvented by a model. Whatever it supplies is left out of the
author page's `needs:`, so nothing later writes over it.

That applies when the page is *created*. For a mirror parsed after the library
already exists, `inductor authors --only-adopt` puts the record onto the page
the creator already has. It replaces a field the page marks `generated` and
stops at one it does not — that being either a person's own words or an earlier
source's — and takes the adopted fields back off the generated list, because
they were not. `--overwrite` says to go ahead anyway.

**Leave the source's tags exactly as the source spelled them.** Mapping them onto
the registry is a later, separate step that a model does per creator. Cleaning
them here loses the evidence of what they actually said.

### 1b. Get the mirror, if there is a site

`tools/fetch/` holds three small fetchers: one that mirrors any site, one that
takes WordPress through its REST API instead of its HTML, and one for hosts that
serve a page per recording with the audio on a different domain. Take the
machine-readable seam where a site offers one — a WordPress `media` endpoint
records which post each attachment belongs to, which turns matching write-ups to
audio from a guess into a lookup.

Both failure modes there look like success: a paginated fetch that never
advances the page number gives you one page repeated, and a mirror that was
rate-limited halfway gives you an archive missing its second half in silence.
Count what you got against what the site claims before you parse any of it.

**Reading a creator's bio and picture out of a mirror has three traps, and all
three produce a confident wrong answer rather than an empty one.**

`og:image` is not necessarily the creator: one site's is a stock photo from an
image bank, and the creator's actual avatar is the site icon. Take pictures
only from the creator's own domain, and check the pixel dimensions — a favicon
and the badge of whatever service they link to pass every other test.

A homepage is a shop window, not a biography. Prices, running times and the
teaser for the latest release all extract exactly like prose, and four of five
homepages read this way produced a catalogue rather than a bio. Only an
`about` page is reliably about them. If you must fall back to a homepage,
require the creator to introduce themselves *by name*: a bare first-person
test passes "I am redefining you", which is a line from one recording's
write-up and became somebody's biography.

And no heuristic tells a product photo from a portrait. Look at the pictures
before you commit them.

### 2. Write the parser in `tools/mirrors/`

One file per source, named after it. They are disposable by design: the source
record is the stable interface, the parser is not. Write it, run it, keep it for
when the site changes.

The one thing to know before you open the directory: **find the data seam, and
it is rarely the rendered HTML.** Nearly every platform ships the same page as
something machine-readable, and parsing that instead is the difference between a
parser that survives a redesign and one that does not.

[`tools/mirrors/README.md`](tools/mirrors/README.md) is the rest of it — where
the seam is on each platform, the worked examples, and what a parser owes the
source record. It is kept there rather than here so there is one table to be
wrong rather than two.

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

**An index is not a mirror, and the join is the risky part.** A source that
holds the recordings gives you catalogue and audio together, and matching is a
filesystem walk. A third-party index — a database site, a wiki, a spreadsheet —
holds only the write-ups, so importing from one is a *join* against files you
already have, and the join is a guess that has to be made well. Match on
duration and require the titles to agree, not the other way round: a
near-identical title is exactly what a voice-only cut, a looping edit or an
intro-less version has, and those are different recordings with different
running times. Veto any pair whose durations disagree, make the best candidate
beat the runner-up by a margin, assign one-to-one, and report the rest unmatched.

**Check whether a duration was measured or advertised before trusting it.** An
index quotes both and does not say which. If a creator's running times are whole
minutes almost every time, that is a shop's stated length, not a measurement,
and it can be out by tens of minutes; a creator whose times are whole minutes a
tenth of the time is being measured. Vetoing on advertised figures throws out
correct matches wholesale. But do not then drop the veto — loosen it and keep a
sanity band, because the pairing that a slack veto lets through is a preview
inheriting a full release's write-up. **Direction matters more than size:** a
file *longer* than advertised is usually an intro, outro or bonus, while a file
*shorter* is the preview-or-partial signature and deserves the stricter test.

**A duplicate claim can hide behind an assignment.** When two importers reach
the same file and the matcher assigns one-to-one, displacing pressure pushes the
loser onto its second-best candidate rather than leaving it unmatched. So the
records where two importers collided are exactly the ones to re-check: if every
one of them disagrees about duration, that is the mechanism, not coincidence.

### 4. Ingest

```sh
inductor tagmap --author some-creator        # map their vocabulary onto the registry
inductor run --author some-creator           # media, transcribe, analyse, review, emit
inductor adjudicate                          # rule on any tag the run wants to add
inductor adjudicate --apply --write          # after reading the rulings
inductor retitle --apply rulings.yaml        # a reviewed TitleRulings file
inductor measured                            # tags the instruments settle; --write to apply
inductor duplicates                          # anything imported twice
inductor orphans                             # creator pages and transcripts nothing refers to
hypnotica -s content build -o www --media link
```

**The maintenance commands are opt-in through `--write`, and that is
load-bearing.** `run` and `ingest` write as their whole purpose and take
`--dry-run` to hold off; everything that sweeps the library to correct it —
`adjudicate`, `attribute`, `retitle`, `registry`, `measured` — reports by
default and changes nothing until asked. That is what makes them safe to try:
run it, read what it says it would do, run it again with the flag.

One of them shipped reading `--dry-run` instead, so its plain form wrote, and
somebody checking what it would do added thirteen entries to the registry
finding out. A single command that inverts the convention is worse than no
convention at all, because the value of the rule is not having to check which
kind you are holding.

`run` is a dependency-graph dispatcher, not a loop over stages: it works out
what each recording is still missing and schedules it across lanes — `disk`,
`cpu`, `gpu`, `api`, `batch`, `art` — so transcription on the GPU overlaps with
measurement, analysis and the batched review rather than waiting its turn. It
also builds three artefacts that `ingest --stage` has no name for at all:
`measurements`, `voiceprint` and `cover`.

The library-wide passes that follow — the tag maps, the rulings, the audits, the
reports — are nodes in the same graph rather than steps after it, so they
overlap each other instead of running one cheap pass at a time. Two kinds of
edge earn their keep. `needs` means *must have succeeded*; `after` means *must
have finished*. Almost every maintenance pass wants the second: gate them all on
`needs` and a single failed recording out of thousands blocks the lot, when what
they actually require is only that nothing is still writing. Lanes are widths,
not categories — the lane that rewrites item documents is one job wide, and the
test for whether a pass belongs on it is not how long it runs but whether it
saves a document some other pass also saves.

A run **removes** the orphans it finds rather than only listing them —
`--no-orphans-write` asks for the report alone, and a dry run never removes.
What that sweep may delete is worth knowing before the first time: an item only
goes when the toolchain claimed it *and* its source record is gone, but creator
pages no item names and transcripts pointing at no item go whoever wrote them.

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
- **A submitted review batch is picked up again by itself.** A killed process
  does not cancel one and there is no cancel endpoint, so the reviews are paid
  for either way. Every submission is journalled under the cache, and a later
  `run` takes up anything still marked `submitted` that covers work in hand,
  dropping those recordings from what it submits. It *collects* rather than
  waits, so a batch still running is left for next time and one stale entry
  cannot stall a run. `--wait-unfinished` sits on one anyway; `--recover
  <batch-id>` names one explicitly.
- **`--no-covers`** skips artwork, which needs a running ComfyUI. Covers are off
  in the shipped config; turn them on when you have one.

Two caches make a re-run cheap, both keyed on what the filesystem already knows:
a fingerprint index (device and inode, checked against size and mtime) and an
item index (size and mtime per item file), both under `cache/inductor/`. Delete
either one and the next run is merely slow.

### 5. Recordings with no words in them

A transcript answers "what is said here", and for a great deal of audio the
honest answer is nothing: tone tracks, drones, music, breathing, wordless voice.
A speech model cannot return that answer. Handed audio with no speech in it, it
returns the stock phrases of its training data — `Thank you.`, `You know,`,
`Thanks for watching` — and they arrive looking exactly like a transcript. In
this library that produced ninety-three transcripts of pure invention, thirty
hours of audio, every one of them from the same place: a retry that reran
transcription with the voice gate off whenever the first pass looked too sparse,
and kept whichever result had *more words*. On silence the gate is right and the
retry cannot lose, because invention always beats nothing.

**A stronger speech model is the wrong instinct.** Measured over sixteen
five-minute windows, the larger model returned *fewer* words than the small one
on fifteen of them — it hallucinates less, but it still hallucinates, and on the
one clip with real sparse narration the two agreed to within two words. Nothing
is gained. The gate was never the problem; the keep-test was. Compare
*substantive* words — strip the known residue first — and be willing to record
that a recording has no speech at all.

Then ask the sound instead of the speech, with instruments that fail in
different directions:

- **The spectrum** is arithmetic. No model, no GPU, no network, and for a tone
  track it recovers the whole design: the carrier each ear hears and the
  difference between them, which is the beat the listener feels and which exists
  nowhere in the file. Measure the channels separately — summing them to mono
  manufactures exactly the beat a binaural track does not have, and reports every
  such recording as pulsing when it is doing nothing of the kind.
- **A multi-label ontology tagger** scores each class on its own, so "somebody is
  speaking" does not compete with "there are mouth sounds". That independence is
  what makes it usable as a gate.
- **A zero-shot audio-text model** ranks whatever phrases you hand it, so it
  describes far better and can be given the collection's own vocabulary — at the
  price that it cannot decline.

**A ranking is not an identification, and the margin will not tell you which you
have.** Offered a label set with no word for what it was hearing, the zero-shot
model called sixty silent tone tracks "whispering close to the microphone"; given
a list of household noises it called sixty-five of them "a car engine". The
margin over the runner-up was *larger* for the deliberately wrong vocabulary than
for the right one, so every margin threshold admitted more nonsense than it kept
real answers. Only the absolute similarity separates them. Put a floor on it, say
so in the record when nothing cleared the floor, and never let a forced answer
reach whatever writes the entry.

**Interjections are content, not residue.** `Oh`, `Mm`, `Ah` are what a wordless
recording is made of; counting them as invention mistakes it for a broken one.
Including them here over-counted the damage in this library by a factor of two —
191 transcripts against a true 93 — and would have thrown away correct
transcriptions of moaning and breath. Keep the residue list to training
boilerplate and nothing else.

**A recording with no words in it cannot be keyed by its transcript.** Analysis
and review are cached against a hash of the transcript, and that is the right
key while there *is* one: two copies of a recording, or two encodings, share
their review and the expensive passes are paid for once however many times the
file appears. Record that a file has no speech, though, and its text is empty —
so every wordless recording in the library hashes to the same string. Keyed on
that they do not share a cache, they share an *answer*: one summary, one
synopsis, one spoiler set, written about whichever tone track was reviewed first
and filed against all of them. One library had 124 entries keyed that way
holding 28 write-ups between them — 97 of them the same one, a description of
a fifteen-second clip of room tone and camera shutters.

Nothing reports it. The dedup that stops a batch asking twice about one key does
exactly its job, the review returns, and every entry is filled in. It bites
hardest where it can least be afforded: the one prompt built entirely from what
the audio was *measured and heard* to be, with no transcript in it anywhere — the
pass that exists precisely to describe a recording from its sound alone — ran
once for the whole collection.

Key a wordless recording by its own audio instead. And when the real review
arrives, treat the inherited fields as replaceable even though they are not
empty: the guard that protects what is already there is protecting another
recording's work. Replace only what a pass wrote, never what a person did.

## Tags the instruments settle

Most tags are somebody's claim — the creator's, in the source record, or a
review model's, from reading a transcript. Both are worth having, and neither
can answer "is there a binaural beat in this file", which is arithmetic.

A measurement-derived tag skips the model and the adjudicator both, because
there is no opinion to rule on: a rule either holds of the file or it does not.
What it must not skip is the registry, because a tag with no definition is a
word nobody can browse by and nobody can argue with. Three properties keep that
honest:

- **Every rule names the guard that makes its instrument trustworthy**, and
  declines rather than guessing when the guard fails. A recording whose dominant
  partial wanders has no carrier to report; one nobody ran the tagger over
  cannot be called wordless. Silence is the right answer far more often than a
  tag is.
- **The ruleset is versioned**, and the version is stamped beside the tags it
  produced. Move a threshold and you leave behind tags that were right under the
  old table and are not under the new one; without the stamp there is no way to
  find them again among thousands of entries.
- **A measurement that contradicts a claim does not overwrite it.** It is
  recorded as a dispute, aggregated per creator — because one file is an error
  and forty is a habit, and a creator who labels tone tracks "binaural" when no
  beat is measurable is telling you something about the rest of their metadata
  that is worth more than the correction.

Cap how many one entry may carry. These exist to answer the question a browser
starts with, not to crowd out the editorial tags that answer the rest.

**Look at your own distribution before trusting any threshold.** Half of these
numbers are instrument guards and half are judgements about the material, and
the second half do not travel. "Markedly slower than conversation" is 70 words
a minute against most speech — and against a library of hypnosis whose median
is 94 and whose lower quartile is 74, it describes 21% of the collection and
says nothing about any of it. Moved to 55, roughly the tenth percentile, it
picks out 909 recordings instead of 1,933. Neither number is wrong; only one
of them is about this library. A threshold near the median of your material is
not distinguishing anything, and the way to find that out is to look before
applying, not after.

Keep them in the config rather than the code, so the library can say what it
means. Then record the ones it moved beside the tags they produced: the
ruleset version answers "which code wrote this" and cannot answer "under which
numbers" once the numbers belong to the library, and an entry tagged under a
threshold that has since moved is only findable if it says so.

**Check what your registry already calls each of them before you apply any of
it.** A ruleset arrives with names of its own, and a vocabulary that has been
growing for a while has words for half of them: `Whispers` where the rule says
`Whispered`, `No Words` where it says `Wordless`, `Minimal Speech` where it
says `Sparse Speech`. Leave those alone and the pass forks the vocabulary —
two whisper tags, three thousand recordings split between them, and nobody
able to browse by whispering.

The dispute is the part that fails silently. A claim is only ever contradicted
by a rule awarding *the same string*, so a rule spelled `Whispered` cannot
dispute a single one of the 1,930 entries claiming `Whispers`. Here that left
the whole mechanism running on the two rules whose names happened to match
already: 499 disputes, all of them one of two tags. Mapping the three names
onto the library's own spellings took it to 1,849, and dropped the additions
from 2,412 to 1,922 because five hundred of them turned out to be tags the
entries already carried. `measured.tags` in `inductor.yaml` is where that
mapping goes; an empty value there switches a rule off entirely.

**A rule gated on a field most of your library does not have awards nothing,
and says so nowhere.** Two of the fifteen rules here test the transcript's
`speech` verdict, which the transcriber only started recording partway through
the library's life: 79 transcripts out of 10,755 carry it. So the rule for "no
words in this at all" can never fire, on a collection with hundreds of
wordless recordings, and the only sign is a tag that never appears in the
tally. When a ruleset reads a field, count how many entries actually have it
before reading anything into a zero.

And be careful what such a rule is allowed to name. Pitch is measurable and
pitch is still not gender: a rule naming the speaker's is a judgement wearing a
measurement's clothes. So is any rule whose threshold you cannot defend — leave
it unwritten until you have calibrated it against recordings somebody has
actually listened to.

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
- **`provenance.managed_by`** is Inductor claiming an entry it produced from a
  source record, and it is what makes deletion safe. Ownership is claimed, never
  inferred: an entry without the stamp belongs to whoever wrote it, so when its
  source record disappears Inductor reports it and stops. An entry *with* the
  stamp goes when its source goes, which is what lets deleting a source entry
  delete what it made. Absence of a claim is a hard stop, not a default.
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
  --write` normalises a tree that predates this. **The symlinks under `media/`
  follow the same rule and are the half that a move actually breaks**: a stale
  reference is reported by `check`, while a stale link is a cover that silently
  stops existing, and the only sign of it is a site build reporting artwork it
  cannot find. `paths --write` repairs those too, matching the longest tail of
  each dead target against the tree, and reports the ones it cannot account
  for rather than pointing them somewhere new.
- **`provenance.generated:`** lists, by field name, what this toolchain wrote
  rather than found — `[cover, spoilers, summary]`. The site marks those lines
  and leaves the rest alone. Nothing is inferred from how a value reads: an
  entry that does not say is left unmarked, because telling somebody their own
  writing was machine-made is the one error worth ruling out. `inductor
  attribute` fills it in for entries that predate it.
- **A creator page can be told rather than guessed.** `_author.yaml` is written
  from the `kind: Author` document in the sources file where there is one, and
  what it supplies is left out of that page's `needs:` so nothing later
  overwrites it. What is not supplied is asked for: a synopsis from a model, an
  avatar from the renderer, both marked in `provenance.generated`. The point of
  the record is that a mirror of somebody's site already has the real thing.
- **`sound:`** is what a recording sounds like, for the recordings that do not
  say anything: the steady tones and the beat between the ears where there are
  any, the sound classes heard in it, and how sure the tagger is that anybody is
  speaking. It sits beside `acoustic:` and is written by the same kind of pass —
  measured into the cache keyed by fingerprint, then applied onto the entries,
  because the site reads `content/` and nothing else. Where a recording has no
  words, this is not a footnote about the entry; it is the entry.
- **An image URL carries a version, the file on disk does not.** A cover is
  served from a path built out of the author and the id, and that path does not
  change when the picture behind it does — so a redrawn cover goes on showing the
  old one in every browser and every service worker that has it. The URL carries
  a short digest of the file's contents (`…/cover.png?v=80a117d9eeb0`). Contents
  rather than a timestamp, so the same picture keeps the same URL after a copy, a
  clone or a restore instead of throwing away a cache that was perfectly good.
- **`cover_prompts:`** holds the image prompt in both styles — `tagged` for
  SDXL-family renderers, `natural` for Flux/SD3-family ones — so changing
  renderer is a flag, not another pass over the library.

## Things that have already cost time

**A batch tagger puts the artist in the title field, and `inductor add` prefers
the tag.** Preferring the tag is still right — it is where a colon and a
subtitle survive, so a file called `GoonerIsland` becomes "Nichole Air: Gooner
Island" — but a title that is only the creator's name is the absence of one,
and two files tagged that way both claim it. The second then gets a numeric
suffix, which reads as a duplicate and is not.

**A variant marker in the filename and not in the title makes two recordings
one.** Two cuts of one session, one with binaural tones and one without, can
share an ID3 title exactly; so can the F4F and F4M dubs. The answer is the
`variant:` field, not a mangled title — take the marker off the filename when
the title does not already carry it. Without it they collide on id, and a
proposed id ending `-2` is a warning, not a resolution.

**The library can hold the preview and not the release.** A site that publishes
a teaser and sells the full recording leaves you with the teaser, and a later
pack turns up with the real thing. A loudness envelope correlates those two at
1.0000 — because the short one is *inside* the long one — which reads exactly
like a duplicate and is the opposite. Compare durations before believing a
perfect correlation.

**Variants correlate as high as re-encodes do.** A loudness envelope cannot see
a binaural bed or a swapped pronoun, so two dubs of one performance correlate
at 1.0000 and a no-binaurals mix at 0.984 — against 0.996 for a genuine
re-encode of a file already held. The figure will not separate them; the
filename and the catalogue will. Decide what a variant is for your library
before you let a number cull anything.

**`inductor add` is for audio with nothing beside it.** It reads ID3 and the
filename, and that is all there is. Where a mirror exists the mirror knows the
titles, the write-ups, the dates and the URLs; reaching for `add` because it is
one command imports a pack named after its files and hands a model the job of
inventing descriptions it had no need to invent. Write the source records.

**A verdict is not a value, and a model will put one in the value's field.**
Asked to review a whole library one item at a time — is this title right, does
it belong to a series, is it a variant — a model answers the question rather
than filling the field: the literal string `it's fine` arrives where the title
goes, thousands of times. Applying that field as written renames thousands of
records to "it's fine". Two quieter shapes mean the same thing: an answer that
restates the existing value verbatim, and an empty one. Normalise a review
before applying any of it, so the value field is non-null *only* where something
actually changes and the verdict lives in its own field. Check the other fields
for the same hazard while you are there, and check no real value resembles the
sentinel before separating them by string.

**A model answers each question independently, so its answers can contradict.**
In the same review, four hundred titles were flagged as garbage — hex ids,
truncated names, collapsed separators, all correctly — and all but one of those
rows *also* said the title was fine. Neither answer is unreliable in general;
what is unreliable is assuming one verdict constrains another. Cross-tabulate
the fields before trusting any of them, and when two disagree, work out which
question the evidence actually answers.

**Do not let a check warn about what the design does.** A variant group shares
one title across its members — that is what makes it a group — so a check that
reports every repeated title fires on hundreds of correct records, tells
somebody to go and fix the thing the library is deliberately doing, and buries
the handful of repeats that really are duplicate imports. Key such a check on
the whole identity, not the part that is meant to repeat.


**One file under two mount spellings defeats every string-keyed match.** A
bind mount, a volume alias, a symlinked share: the same bytes, the same inode,
two paths. Anything that matches records by comparing path strings will treat
them as unrelated, and the symptom is not an error but two complementary lists
that never overlap -- records that look orphaned on one side, files that look
unimported on the other. Test it with `stat -c %d:%i` on both spellings before
believing either list. Key on device and inode where you can; where you cannot,
normalise to the alias, which outlives the volume being re-provisioned.
Normalising may also make real collisions visible for the first time -- a
mismatch that hides a duplicate is worse than the duplicate.


**A refusal is a fact about the model, not about the material.** A model that
will not describe what you gave it answers with prose, with an empty body and an
error finish reason, or with an outright error — and all three arrive downstream
as a result that will not parse, indistinguishable from a mangled one. Do not
treat that as a bad recording. Name one or more fallback models, offer the
leftovers to them directly rather than at batch latency, and record which model
actually answered, because that provenance is part of the entry. When every
model declines the same item, stop: an agreed refusal is a thing to read, not an
obstacle to route around.

**A pass that rewrites whole documents belongs on the single-file lane.** A pass
that reads a document set when it starts, edits in memory, and saves each whole
document back will silently lose whatever another pass wrote in between — no
error on either side, and the symptom is an intermittently missing field rather
than a failure. The test for whether a pass needs serialising is not how long it
runs but whether it saves a document some other pass also saves.


**A "is it already done?" predicate must answer the *producer's* question.**
If the scheduler decides an artefact is missing by probing one path and the
worker decides by consulting a field on the record, the two will disagree, and
the disagreement is silent: work gets queued, the worker declines it, nothing
errors, nothing changes. The symptom is not a failure — it is a count that never
goes down and a run that is always slower than it should be. Whenever a
scheduler and a worker both decide whether work is needed, make them ask the
same question, and prefer the record's own declaration over a guessed filename:
an artefact that arrived with the source may not use the extension or the
spelling the generator would have chosen.


**A font can report a glyph and then draw nothing.** One of the faces here
returns a valid glyph index and a correct advance width for most of its
lowercase, and rasterises an empty outline — no error, nowhere. Because the
advances stay right, the letters that survive are spaced as though the missing
ones were there, so what comes out reads as a word rather than as damage: one
creator's name was set as "CesS", another's as "Ct". Measure every character
before committing to a face. Three faces turned out to be implicated across 876
pictures rather than the one that was obvious, the third failing only on titles
containing a sharp sign — so ask per picture, not per font, and a face that can
set most names is worth keeping for them.

**A stamp has to record what produced the thing, not what was asked for.** The
artwork stamp held the prompt, the renderer and the words, and not the face they
were set in — which is the one field that differs exactly when a picture has gone
wrong, because the face is substituted only when the requested one cannot draw
the text. A picture ruined that way was indistinguishable, to every check there
was, from one drawn perfectly. Whatever chooses the outcome belongs in the record
of it; anything else is a record of the request.

**A control character survives every cleaner you have.** A `\x04` in the middle
of a word reached a library from a rip and sat there through every pass: not
whitespace, so nothing trimmed it; not punctuation, so nothing cleaned it; and it
slugs away to nothing, so the filename looked perfect. It surfaced only where six
fonts in turn were asked for a glyph and none of them had one. Strip control
characters where text enters, and leave everything above ASCII alone — the same
pass must not touch an accent, a dash or a script it does not recognise.

**A field written by several passes over several years holds several
vocabularies.** One recording's "where did this transcript come from" held six
different things across the library: a model name, a model name with a flag after
it, the word "transcript", the word "None", the word "whisper", and "source".
Three of those say nothing about provenance, and the page was reading anything
that was not "source" as "automatic" — asserting to the reader something nobody
had recorded. When a field has drifted, say what is known and stop: "how it was
made was not recorded" is a true sentence and "automatically generated" is not.

**Prose is not preformatted.** A transcript that arrives with the recording has
no timestamps, so it fell through to the branch that renders a block of `<pre>` —
and a supplied transcript is one paragraph per line with lines running to five
hundred characters, so the panel became a wall of monospace that scrolled
sideways. The fallback branch of a renderer gets the material the main branch was
not designed for, which is exactly the material worth looking at.

**A refusal has to be written down, or it is not a decision — it is a question
asked again every run.** A pass that looks at a recording and correctly concludes
there is nothing to make must record that conclusion somewhere the scheduler
reads, or the scheduler will keep asking. Two hundred and seventy recordings were
re-examined on every run, for ever, because "too little transcript to analyse"
lived only in the return value. Key the refusal to whatever it was a judgement
about — here the transcript — so it expires by itself when that changes, and no
stale refusal outlives its reason.

**Declining is not failing, and reporting it as failure buries the real ones.**
"Nothing on disk to write an entry from" and "the batch never came back" want
different words in the log. Forty-eight of the first printed as hard failures and
made the run look broken; the handful of genuine failures were indistinguishable
in the noise.

**A repair that writes to a different name than the finder looks for never
takes.** A damaged `.m4a` was repaired by re-encoding to `.mp3` — and the routine
that answers "where is this recording placed?" preferred `.m4a`. So the repair
landed *beside* the broken file and was never consulted: the check stayed
unsatisfied, the re-encode ran again on every run, and the site went on serving
the damaged copy. Whoever writes the fix and whoever looks for it must agree on
the name. When a fix supersedes something, remove what it replaced — but prove
identity first: a shared filename is no evidence of a shared recording, and two
source records can collide on one, so require the file you are about to delete to
be demonstrably the same one you just rewrote.

**Use the identity the library records, not one you can recompute.** A resume
point stored a computed `<author>-<stem>` id while everything else matched on the
entry's declared `id:`. They agree only until a filename carries its own author
prefix — `somecreator/somecreator-third-session.yaml` computes to
`somecreator-somecreator-third-session` — and then the saved list names nothing
and takes the whole resume with it. If a document declares an identifier, that is the
identifier.

**A value that prints like a number and compares like a string rewrites your
library every run.** Caches decoded with `UseNumber` keep an integer an integer,
but `json.Number` is a string type, so the YAML writer quoted every measured
figure — `beat_hz: "8.05"` — and reading it back gave a string that never
compared equal to the float that produced it. The equivalence check said "changed"
on 5,850 entries, on every run, and rewrote them all. Nothing errored. It showed
the way these always show: a count that never falls.

**Compiling is not installing.** `go build ./...` type-checks and writes no
binary; the tool on your `PATH` is whatever was last built to `bin/`. A whole
afternoon of "why is my change not taking effect" was two separate instances of
this, in two repositories, on two different days — the second one after the
lesson was already written down for the first. Check the binary's timestamp
before you debug anything else.

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

**What is missing from the library is often missing on purpose.** Before writing
an importer for an archive that looks unharvested, measure what it would actually
add. One shop mirror here held ninety-two files and none of them were in the
library, which looked like an oversight worth a hundred lines of parser: ninety
of the ninety-two are named `sample-` or `-DEMO`, ninety-one run under five
minutes, and exactly one is a release. The shop sells the recordings and mirrors
the previews. Across five such archives, 269 unimported files turned out to be
244 previews and about 25 real recordings — and an importer without a duration
floor would have added all 269 as though they were releases. Count what you would
gain before you build the thing that gains it; the answer here was 34 write-ups
and some fifty recordings, not the fourteen hundred the file counts suggested.

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

**A file can open, report a duration, and still be broken.** A truncated
download or a damaged frame run decodes to silence: it transcribes to a few
characters, passes every cheap check, and becomes an item that looks complete
and plays as nothing. Inductor decodes each recording end to end before placing
it, caches the verdict beside the fingerprints, and the `media` stage refuses
audio that fails — everything else in the graph depends on `media`, so a broken
file is stopped before anything processes it. Sampling the opening seconds does
not find this; the damage is usually further in, and half a file is worse than
none.

**A corrupt copy defeats a loudness envelope.** The envelope is computed from the
audio, so a damaged duplicate of a recording already held correlates with nothing
and reads as new — the dedup keeps it *because* it is broken. Check that audio
decodes before trusting any acoustic comparison of it.

**A cache that is not there reports every recording as untranscribed.** Tools
have resolved paths that had stopped existing and raised nothing: `rglob` on a
missing directory returns nothing, and a missing author file just means a name
never gets filled in. One enrichment run sent the model `some-creator` instead of
`Some Creator` for every item, and nothing said so. Ask by declared id, and when
a scan returns zero, check the directory before believing it.

**A `--dry-run` that calls models still spends money.** It means "write nothing",
not "do nothing": it analyses and submits the review batch. A killed process does
not cancel a submitted batch, but it no longer costs twice: the next `run` finds
it in the journal and takes it up.

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
