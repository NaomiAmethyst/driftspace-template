# state/decisions/ — what a person decided, and why

The one part of `state/` that is written by hand, read by hand, and worth
reading. Everything else in the pipeline can be re-derived; a judgement cannot.

Two kinds of file live here.

## Tag maps, one per creator

Written by `inductor tagmap --author <creator>`, which shows a model every tag
that creator used and asks what it should become in `content/tags.yaml`. The
verdicts are `map`, `drop`, or a new registry entry.

```yaml
author: some-creator
model: anthropic/claude-opus-5
mapping:
  - tag: Vocal
    verdict: map
    to: Voice Kink
    why: bare word for the voice as the draw; nearest existing entry
  - tag: 'Production: No Binaurals'
    verdict: map
    to: 'Production: No Binaural'
    why: plural spelling of an existing tag
  - tag: Blues
    verdict: drop
    why: >
      the ID3 genre byte, not a tag: it reached 205 recordings across 28
      creators and not one of their transcripts is about the blues.
```

**Read the map before applying it.** A model that maps a creator's whole
vocabulary onto three registry entries has lost the distinctions that made the
vocabulary worth having, and a model that proposes forty new entries has lost
the point of a registry. Edit the file; it is the record.

## Rulings

`inductor adjudicate` rules on tags a run wanted and could not have, because they
are not in the registry. Read the rulings, then apply them:

```sh
inductor adjudicate                    # what is pending
inductor adjudicate --apply --write    # fold them into the registry and the items
```

## Anything else a person settled

A duplicate group the ranking could not call, a title two sources disagree
about, a creator whose name is spelled three ways. Write it down here, with the
reason, in the same shape:

```yaml
apiVersion: inductor/v1
kind: Decisions
keep:
  - path: some-creator/the-black-onyx.yaml
    why: >
      The only one of the three with a source_url, and it is the creator's own
      page. The others are archive filenames, one of them a typo.
```

**The `why` is the file's reason for existing.** Without it a later session
quietly undoes the decision, re-runs the ranking, and gets the other answer. The
data does not contain what a person knew.
