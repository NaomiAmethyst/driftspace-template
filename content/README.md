# content/ — the library

The only thing here that matters long-term. Everything else in this directory
tree can be rebuilt from it; it cannot be rebuilt from anything else.

```
hypnotica.yaml              site configuration
tags.yaml                   the tag registry
<creator>/_author.yaml      kind: Author
<creator>/<title>.yaml      kind: Item
<creator>/<title>.transcript.yaml   kind: Transcript
```

Inductor writes these; Hypnotica reads them. Neither owns them — the documents
are portable YAML and hand-written entries work fine.

## Every document declares itself

```yaml
apiVersion: hypnotica/v1
kind: Item        # Item | Author | Transcript | Config | Tags
```

**Never infer a document's type from its path.** Hypnotica will fall back to
filename heuristics for old hand-written libraries, but anything written here
states its kind. That assumption has broken repeatedly.

## Items

Required: `title` and `author`. Everything else is optional, and an item that is
missing things says so in `needs:` rather than guessing.

```yaml
apiVersion: hypnotica/v1
kind: Item
id: some-creator-learning-to-listen     # global, and permanent
title: Learning To Listen
author: some-creator
audio: ../../media/audio/some-creator/learning-to-listen.mp3
cover: ../../media/cover/some-creator/some-creator-learning-to-listen.png
duration: 1492.9
date: 2025-11-18
series: A Series Of Theirs
tags: ['Voice: fem', 'Induction: Visualisation', Femdom, Trance]
categories: [Audio, Hypnosis]
summary: One sentence, for the card.
description: |
  <p>Several paragraphs, for the page.</p>
explicit: true
spoilers:
  - severity: medium          # low | medium | high
    disclosure: declared      # whether the recording says it is doing this
    confidence: high
    timestamp: 0:19:11
    trigger: |
      plush
    effect: |
      Drops the listener into trance whenever the speaker says the word.
    quote: |
      Or even if I type the word plush, do welcome to this relaxation.
provenance:
  source_record: some-creator.yaml
  fingerprint: 17148f15d758f8e8207e6dbf726636a5
  generated: [cover, description, spoilers, summary, tags]
acoustic:
  seconds: 1492.9
  f0_median_hz: 177.8
  voice: fem
cover_prompts:
  tagged: massage table in a soft pink boudoir, warm candlelight, ...
  natural: A massage table draped in silk inside a dimly lit boudoir, ...
```

**`id` is global across the library**, so it carries the creator. Filenames come
from the title and may change; ids do not. Once items reference an id, changing
it breaks playlists, resume positions and offline downloads in anyone's browser.

**`spoilers:` is the point of the whole exercise.** It names what a recording
installs, with the sentence that installs it, so somebody can decide before
playing rather than after. The site keeps it behind a visibility control.

## Provenance

`provenance.generated:` lists, by field name, what this toolchain wrote rather
than found. The site marks those lines and leaves the rest alone.

**Nothing is inferred from how a value reads.** An entry that does not say is
left unmarked, because telling somebody their own writing was machine-made is the
one error worth ruling out. `inductor attribute` fills this in for entries that
predate the convention.

`provenance.proposed_tags:` holds tags a model wanted and could not have, because
they are not in the registry. They sit there until `inductor adjudicate` rules.

`provenance.measured_tags:` records the tags the instruments settled on this
entry, and the version of the ruleset that settled them:

```yaml
provenance:
  measured_tags:
    ruleset: 1
    thresholds: {slow_delivery_wpm: 55}   # only what this library moved
    tags: [Production: Binaural, Production: Theta Beat]
```

It is kept for two reasons. A tag this pass awarded and no longer awards is one
it may take back; a tag somebody else asserted is not, and without the record
there is no telling them apart. And when a threshold moves, these are the only
way to find the entries tagged under the old table. The version covers a change
to the code; `thresholds` covers a change to the numbers, which live in
`inductor.yaml` and so cannot be read off the version at all. An entry carrying
`ruleset: 1` after the rules reach 2, or carrying a threshold the config no
longer sets, is one to look at again — and there is no re-deriving nine
thousand recordings to work out which those were.

## Tags

`tags.yaml` is the registry, and the **only** source of tags. A tag that is not
in it never reaches an item. Eight kinds:

```
Voice: fem            how the speaker presents
Audience: man         who is addressed
Induction: Fixation   how trance is brought on
Production: Whispers  how the audio was made
Trigger: Sink         a cue it installs            (behind the spoiler gate)
Compulsion: Relisten  a drive it leaves behind     (behind the spoiler gate)
CW: Death             what it touches on rather than is about
Femdom                what happens in it — a bare tag, no prefix
```

The registry shipped here is a starting point, not a standard. Extend it, cut
what does not apply, and rewrite the definitions to mean what you mean — but
extend it *through the pipeline*, so the decision is recorded:

```sh
inductor tagmap --author some-creator    # map a creator's vocabulary onto it
inductor adjudicate                      # rule on what a run wants to add
inductor adjudicate --apply --write      # after reading the rulings
```

Letting unruled tags sit on items is how 874 unregistered spellings accumulated
across 558 items in one library. `state/decisions/` is where the rulings live and
why.

**Quote any tag name YAML would read as a number or a boolean** — `'69'`, not
`69`. One unquoted numeric key makes its entire block parse as a non-string map,
which Inductor reads as empty: every tag in that block silently stops resolving,
and a registry write can then overwrite the block with nothing. Check with
`inductor` itself rather than by eye — a source record tagged with something you
know is registered should come back in `tags:`, not in `provenance.proposed_tags`.

Two distinctions in the shipped registry are load-bearing:

- **`Audience: sissy` is not `Audience: transfem`.** One is a kink about being
  made into a woman; the other is a woman. Conflating them files recordings that
  call the listener a feminised male under a trans audience, where a trans woman
  browsing for herself finds them.
- **`CW:` is for what a recording *touches on*; a bare content tag is for what it
  is *about*.** Snuff is content because killing is the draw; `CW: Death` is a
  warning because somebody dies in the story.

## Working on this directory

Use Inductor commands rather than editing hundreds of files by hand — `retag`,
`fold`, `retitle`, `paths`, `attribute`, `authors`, `duplicates`, `orphans`. A
hand edit across the library leaves no record of what was decided, and the next
run may undo it.

```sh
hypnotica -s content check     # kinds, author references, unique ids
inductor check                 # source records against what is here
```

Paths inside an item are written **relative** — `../../media/audio/...` — so the
whole library can be moved or cloned. Anything outside it stays absolute.
`inductor paths --write` normalises a tree that predates this, and relinks the
symlinks under `media/` by the same rule — see `media/README.md`, because those
are what a move breaks without telling you.

## A real one

[`examples/sleepytime-trance.item.yaml`](../examples/sleepytime-trance.item.yaml)
is a finished entry — tags, spoilers, acoustics, provenance and all — beside the
source record it was built from.
