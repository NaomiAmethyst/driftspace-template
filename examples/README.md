# examples/ — one recording, all the way through

The READMEs elsewhere describe the *shape* of each document. This is one real
recording in all of them at once, so you can see what the pipeline actually
does — which is most legible as the difference between two files:

| | |
|---|---|
| [`sleepytime-trance.source.yaml`](sleepytime-trance.source.yaml) | what a parser knew: the creator, then the recording |
| [`sleepytime-trance.item.yaml`](sleepytime-trance.item.yaml) | what the library holds afterwards. 12 KB |
| [`sleepytime-trance.transcript.yaml`](sleepytime-trance.transcript.yaml) | an excerpt of what was heard |
| [`_author.yaml`](_author.yaml) | the creator page |
| `sleepytime-trance.cover.jpg` | the artwork |
| `naomi-persephone-amethyst.author.jpg` | the creator's photograph |

The recording itself is at
<https://amethyst.name/sleepytime-trance>, and was posted to
[r/QueerEroticHypnosis](https://www.reddit.com/r/QueerEroticHypnosis/comments/1p70ryn/f4a_sleepytime_trance_noneroticpmrsleepinsomnia/).

Nothing here is wired into anything. `content/` and `sources/` are what the
tools read; this directory is documentation, and you can delete it.

The recording is the template author's own, non-sexual, and already published,
so it can be reproduced here in full. That is the only reason it is this one:
everything else in a library like this belongs to somebody else.

## What the run added

The source record carried thirteen fields. The item has eight more:

    id  tags  spoilers  script  acoustic  cover  cover_prompts  sound

`inductor run` transcribed it, measured it, put it to a model, and wrote the
result back. Read the source and the item side by side once; it is the clearest
statement of what the pipeline is for.

## What it did not do, and how you can tell

**`provenance.generated` names the machine's work and nothing else:**

```yaml
generated: [cover, spoilers, summary]
```

The `description` is not in that list, because `description_from_source: true` —
the creator wrote it, in her own posting, and it is passed through untouched.
Neither is `script`, because that arrived with the recording
(`has_author_script: true`). Both sit in the same document as two
machine-written fields, and the only thing separating them is that list. Nothing
is inferred from how a value reads: telling somebody their own writing was
machine-made is the one error worth ruling out, so an entry that does not say is
left unmarked.

That flag is load-bearing, which is why it has to be right. The review pass is
shown the description as *the creator's own words*, so it can judge whether a
suggestion was disclosed to the listener. Hand it a description this pipeline
wrote and the model grades disclosure against its own earlier output, and
everything comes back "declared". This very entry had that wrong once: an
importer copied a generated write-up into the source record and marked it as the
creator's, and it took the creator reading the file to catch it. A field that
asserts provenance is worth exactly what the care behind it is worth.

**The audio is not here** — it is a 28 MB mp3 and does not belong in a git
repository. `audio:` points where it would point in a real library, and the file
itself is linked from the page above.

**The pictures are deliberate, and that is the point.** The cover is the
creator's own artwork with the house nameplate drawn over it by the same
routine the pipeline uses, in the face her creator page names. So
`provenance.generated` does *not* list `cover` here. In the real library a model
drew that picture and the list says so — but a template arguing for marking
machine-made work should not have a machine-made picture as its only
illustration. `cover_prompts` is recorded either way: the prompts were written,
they just were not used for this one.

The author page is the same lesson from the other side. Its photograph, links
and language came from the `kind: Author` record in the source file, so nothing
on it was machine-written and it carries no `generated` list at all. Without
that record the pipeline would have had a name and nothing else, and would have
asked a model for a synopsis and drawn an avatar — both strictly worse than what
her own site already said.

## What the tags were before they were tags

The source record keeps the posting's own words:

```yaml
also_titled: ['[F4A] sleepytime trance [non-erotic][PMR][sleep][insomnia]']
tags: [F4A, non-erotic, PMR, sleep, insomnia]
```

None of those are registry tags and the parser does not pretend otherwise. In
the item they have become `Voice: fem`, `Audience: anyone`,
`Induction: Progressive Muscle Relaxation`, `Sleep`, `Non-Sexual` — by way of
`inductor tagmap`, which rules on one creator's vocabulary as its own step, and
`inductor adjudicate`, which rules on anything a run wants to add. Cleaning them
in the parser would have thrown away the evidence of what was actually posted,
and `[F4A]` carries two separate facts that one tag cannot hold.

## The script and the transcript are the same words twice

`script:` is what the creator wrote and read out. The transcript is what a
speech model heard her say. Comparing them is the cheapest demonstration of what
transcription costs — the ellipses and the pacing go, the numbers of a countdown
come back as digits or words depending on the model's mood, and `PMR` is never
`PMR`. The transcript records which model produced it, and no entry in the
library treats one as the other.

Not every recording comes with a script. This one does because the creator wrote
it first and published it alongside the audio, which is the ideal case and
rare — most of the library has only the transcript.

## The spoiler is the part worth reading

```yaml
severity: high
disclosure: declared
trigger: Listening to the recording again
effect: |
  Conditioned sleep onset that compounds with repetition: every future listen is
  suggested to drop you into trance faster …
```

This is a gentle, non-sexual sleep file, and it still carries a **high** finding.
That is the grading working as intended: severity is about *reach*, not about how
strong the material is. A suggestion that compounds every time you play the file
follows you out of the session, so it is high — and `disclosure: declared` records
that the creator says so plainly at the start, which is a different question and
deservedly a separate field. A mild recording can hold a high finding, and a
fierce one whose every effect ends on waking is low.

Note also that the finding quotes the recording verbatim and carries the
timestamp of the line it quotes. A claim about what a file will do to somebody is
only worth having if it can be checked.

## Where each of these lives in a real library

```
sources/<creator>.yaml                     the source records, one document each
content/<creator>/<stem>.yaml              the item
content/<creator>/<stem>.transcript.yaml   the transcript, keyed by `item:`
content/<creator>/_author.yaml             the creator page
media/audio/<creator>/<stem>.mp3           what the site serves
media/cover/<creator>/<id>.png             the artwork
```

The stem comes from the title; the id carries the creator and does not change.
They part company as soon as a title is corrected, which is why
`content/README.md` has a section about it.
