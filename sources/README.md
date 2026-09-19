# sources/ — what some parser managed to learn

One YAML file per creator, holding a `kind: Source` document per recording,
`---` separated. This is the stable interface between "whatever shape the
material arrived in" and the rest of the pipeline: parsers are disposable, source
records are not.

```yaml
---
apiVersion: inductor/v1
kind: Source
audio: /path/to/Some Recording.m4a      # required
title: Some Recording                   # required
author: Some Creator                    # required
date: 2025-11-18
series: A Series Of Theirs
duration: 1492.9
description: |
  <p>Whatever the site said, kept as they wrote it.</p>
tags: [Femdom, Hypnosis]                # their words — do not clean them
categories: [Audio, Hypnosis]
source_url: https://example.com/some-recording/
explicit: true
---
apiVersion: inductor/v1
kind: Source
audio: /path/to/Another Recording.mp3
title: Another Recording
author: Some Creator
```

Only `audio`, `title` and `author` are required. Everything else is whatever the
source actually said; leave out what it did not say. **Prefer no metadata to
wrong metadata** — `needs:` gets filled in later, and a wrong description is
silent and permanent.

## Two rules that matter

**Leave the source's tags exactly as the source spelled them.** `Femdom Erotic
Hypno`, `femdom-hypnosis` and `FEMDOM` all stay as they are. Mapping a creator's
vocabulary onto `content/tags.yaml` is a separate step that `inductor tagmap`
does per creator, and it needs to see what they actually wrote. Cleaning here
destroys the evidence.

**Audio paths point at the originals.** Absolute paths for anything outside this
directory — a read-only archive mount, an external disk. Relative paths resolve
from the source record's directory and then the source tree. Nothing here copies
or modifies the audio; `inductor run` installs it into `media/` as a symlink by
default.

## Getting records in

For a plain folder of audio with nothing else alongside it:

```sh
inductor add ~/audio/some-creator/*.mp3 --author-name "Some Creator" --dry-run
inductor add ~/audio/some-creator/*.mp3 --author-name "Some Creator"
```

`add` reads ID3 and durations and writes the records for you. For anything with a
site mirror, a pack README or a spreadsheet behind it, write a parser —
[`tools/mirrors/README.md`](../tools/mirrors/README.md).

## Then check

```sh
inductor check
```

Parsers fail by producing well-formed YAML about the wrong data, which looks
exactly like success. `check` reports the record count per creator, missing
audio, and duplicate claims on the same file. Read those numbers against what
you expected before you spend a transcription run on them: a shop that says 971
products and a source file with 35 records means you found the listing page, not
the catalogue.

## Saying who the creator is

A sources file may also hold one `kind: Author` document. A mirror of somebody's
site has their bio, their picture and their links sitting right there, and
without somewhere to put them the pipeline discards all three and then asks a
model to invent a synopsis and draw an avatar — both strictly worse than what
the site already said.

```yaml
---
apiVersion: inductor/v1
kind: Author
name: Some Creator
url: https://some-creator.example
links:
  website: https://some-creator.example
image: /path/to/their-avatar.jpg
description: |
  <p>What they say about themselves, as they wrote it.</p>
language: en
```

Only `name` is required; the id is slugified from it unless you give one.
Anything supplied here lands on `content/<creator>/_author.yaml` and is left out
of that page's `needs:`, which is what stops a later pass writing over it. It is
not marked generated either, because it was not.

## A real one

[`examples/sleepytime-trance.source.yaml`](../examples/sleepytime-trance.source.yaml)
is an actual source record, next to the item it became. The difference between
the two files is what `inductor run` does.
