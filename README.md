# Driftspace

A working directory for building a spoken-audio library with
[Hypnotica](https://github.com/NaomiAmethyst/hypnotica) and
[Inductor](https://github.com/NaomiAmethyst/inductor).

Clone it, point an LLM agent at it, and tell the agent what you have. It reads
the notes in [`CLAUDE.md`](CLAUDE.md) and in each directory, writes a parser for
whatever shape your material arrived in, and runs the pipeline. The end of it is
a static website: every recording with a transcript, a write-up, tags, acoustic
measurements, and a spoiler list naming the triggers and compulsions it contains.

The spoiler list is the point. Hypnosis recordings try to do things to the
listener, and a catalogue that says what lets you decide before you play
something rather than after.

**This template ships no recordings and no metadata about any.** It is a layout,
a tag vocabulary, and a set of working notes.

## What it is made of

Three pieces, and keeping them separate is the point.

| | |
|---|---|
| `content/` | the library itself: YAML, and the only thing that matters long-term |
| Hypnotica | turns `content/` into a website. Knows nothing about where it came from |
| Inductor | fills `content/` from audio. Knows nothing about websites |

Each tool is usable alone. Hypnotica will build a site from YAML you wrote by
hand. Inductor will enrich a folder of audio and hand you YAML to do what you
like with. Together they are a pipeline.

## Install the tools

Both are single Go binaries, and both want FFmpeg on `PATH`.

```sh
git clone https://github.com/NaomiAmethyst/inductor
cd inductor && go build -o ~/.local/bin/inductor ./cmd/inductor

git clone https://github.com/NaomiAmethyst/hypnotica
cd hypnotica && go build -o ~/.local/bin/hypnotica ./cmd/hypnotica
```

| | needed for |
|---|---|
| Go 1.26+ | building either binary |
| FFmpeg and ffprobe | durations, conversion, acoustic measurement |
| Python 3.10+ | transcription and voiceprints — on the worker machine only |
| An NVIDIA GPU | transcribing at a sensible speed. A CPU worker is the fallback |
| An OpenRouter key | write-ups, tags and spoilers. `OPENROUTER_API_KEY` |
| ComfyUI | cover art. Optional, and off by default |

Nothing but Go and FFmpeg is needed to import material, tag it, and build a
site. Transcription and enrichment are what pull in the rest.

## Start

```sh
git clone https://github.com/NaomiAmethyst/driftspace-template my-library
cd my-library && rm -rf .git && git init
```

Then edit two files — `inductor.yaml` for models and paths, and
`content/hypnotica.yaml` for the site's name and URL — and say something like:

> I have a folder of mp3s at `~/audio/some-creator/` and a mirror of their site
> at `~/mirrors/some-creator/`. Import them.

The agent's route from there is written down in [`CLAUDE.md`](CLAUDE.md). If you
would rather drive it yourself:

```sh
inductor add ~/audio/some-creator/*.mp3 --author-name "Some Creator"
inductor check                      # before trusting anything a parser wrote
inductor tagmap --author some-creator
inductor run --author some-creator --no-covers
inductor adjudicate                 # rule on tags the run wants to add
hypnotica -s content check
hypnotica -s content build -o www --media link
hypnotica serve -o www -p 8080
```

`--media link` symlinks the audio into the site instead of copying it, which
matters once the library is larger than the disk has room to duplicate.

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

## The layout

Every directory here has a `README.md` saying what belongs in it. Directories
that are meant to start empty hold a `.gitkeep` and nothing else.

```
content/            the library. Permanent, and the only thing that matters
  tags.yaml           the tag registry: the only tags that may reach an item
  hypnotica.yaml      site configuration
media/              audio and artwork, placed where the site can serve them
sources/            source records, one YAML per creator

state/              produced by the pipeline. Expensive, and not disposable
  decisions/          tag maps and rulings: what a person decided, and why
  transcripts/        what was heard, keyed by the audio's fingerprint
  enrichment/         what the models made of it, keyed by the transcript's

cache/              indexes, measurements, staging. Safe to delete
tools/mirrors/      one parser per source site
tools/import/       one-off importers and migrations
www/                the built site. Generated; never edit it
```

`cache/` may be deleted; `state/` may not, and neither may `content/`. The line
between them is not how the files were made but what it would take to make them
again: a voiceprint is GPU-hours and a tag ruling is a judgement nobody can
reconstruct.

## Git, and the parts of this that git is wrong for

`.gitignore` excludes `cache/`, `media/` and `www/`, and carries commented lines
for `state/` and `content/` — see the comments there, because whether those
belong in git depends on how private the library is and how large it has grown.

**The audio does not belong in git**, and neither does the artwork. A few
thousand recordings is a few hundred gigabytes, git stores every version of
every one of them forever, and no forge will take it. Options, roughly in order
of how much trouble they are:

- **Leave it out.** `media/` is symlinks into wherever the audio already lives.
  Back that directory up the way you back up anything else — `rsync`,
  `restic`, `borg`, a second disk.
- **[git-annex](https://git-annex.branchable.com/)**, which keeps the file
  contents outside git and the filenames inside it. The closest fit: it is built
  for exactly this, and it can track which drive holds which copy.
- **[Git LFS](https://git-lfs.com/)**, if you are pushing to a forge that offers
  it and can live with its quotas.
- **[Syncthing](https://syncthing.net/)** or similar, alongside the git repo
  rather than inside it.

The YAML is what is worth versioning. It is small, it is the expensive part to
rebuild, and its history is a record of what you decided about each recording.

## Privacy

This is a personal library, and the default configuration treats it as one.
`base_url` points at localhost, the site is static and needs no server-side
anything, and nothing is published until you publish it.

What does leave the machine: transcript text and metadata go to whichever models
`inductor.yaml` names, over OpenRouter. Transcription and acoustic measurement
are local. If the material is sensitive enough that model providers are a
problem, run the ingest stages without `analyse` and `review` and write the
entries yourself — `inductor ingest --stage media --stage transcribe --stage emit`.

## Licence

Copyright © 2026 Naomi Persephone Amethyst <naomi@amethyst.name>.

This template — the layout, the notes and the tag registry — is **GNU GPL
version 3 only**, matching [Hypnotica](https://github.com/NaomiAmethyst/hypnotica)
and [Inductor](https://github.com/NaomiAmethyst/inductor), neither of which is
included here. See [`LICENSE`](LICENSE).

The library you build with it is yours. The licence covers this scaffolding, not
your recordings, your metadata or anything you write into `content/`.
