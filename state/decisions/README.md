# state/decisions/ — what a person decided, and why

The one part of `state/` that is written by hand, read by hand, and worth
reading. Everything else in the pipeline can be re-derived; a judgement cannot.

Two kinds of file live here.

## Tag maps, one per creator

Written by `inductor tagmap --author <creator>`, which shows a model every tag
that creator used and asks what it should become in `content/tags.yaml`. The
verdicts are `map` and `drop`.

**A row's `to:` may only name a tag the registry already has.** The map says
what a creator's vocabulary becomes *in the registry*; a row pointing at
something the registry has never heard of answers nothing, and the registry
rules on the tag as written instead. Such a row is a fault, not a decision —
`inductor check` lists them under `map_targets_missing`, and each is to be
adjudicated into the registry or dropped from the map.

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

**These files carry comments, and the tools do not.** An `inductor registry`
operation that repoints a map — a rename or a merge whose target the map names —
rewrites the file from its parsed contents, which does not preserve comments.
If a map's header is worth keeping, keep a copy, or put the note somewhere the
tools do not write.

**Read the map before applying it.** A model that maps a creator's whole
vocabulary onto three registry entries has lost the distinctions that made the
vocabulary worth having, and a model that proposes forty new entries has lost
the point of a registry. Edit the file; it is the record.

### Targets waiting on a ruling

When the model wants a registry entry that does not exist, `tagmap` does not
write it as a mapping. It goes here instead, in the same file:

```yaml
pending:
  - tag: Humour                  # the entry being asked for
    from: humor                  # the creator's spelling that wanted it
    author: some-creator         # filled in from the filename if absent
    count: 9                     # how many of their recordings use it
    description: Comedy is part of the intent; the recording is meant to be funny.
    why: Playful and Giggles cover tone and sound, not comedic intent
```

`pending:` is a queue, not a mapping — nothing resolves onto these, so no tag
can be placed by a name nobody has ruled on. `inductor adjudicate` reads them
alongside what the items propose. If the entry is approved it joins the
registry and the tag resolves on its own; if it is declined or merged, the
ruling settles it and the queue entry can go.

Why the queue exists: a row that names a tag the registry lacks *reads as
settled*. In one library 100 of them sat across five creators pointing at
`Humour`, `Exercise`, `Strong Woman` — plausible names nobody ever added — and
a single `retag` stripped 1,029 registered tags off 675 recordings before
anyone noticed, because a map used to outrank the registry. It no longer does,
and this is where the proposal waits instead.

## Rulings

`inductor adjudicate` rules on tags a run wanted and could not have, because they
are not in the registry. Read the rulings, then apply them:

```sh
inductor adjudicate                    # what is pending
inductor adjudicate --apply --write    # fold them into the registry and the items
```

## Editing the registry by hand

`inductor registry` is how a person changes the vocabulary without a model in
the loop. Every operation keeps the rest of the library in step — the items
carrying the tag, the `tags_added` a run recorded, the proposals still waiting
on it, and every map row that points at it — and appends a ruling here, so the
next `adjudicate` does not re-open what was just settled.

```sh
inductor registry add "Humour" --description "Comedy is the intent." --write
inductor registry describe "Toys" --description "..." --write
inductor registry remove "Abstract" --why "not a subject anyone browses by" --write
inductor registry rename "humor" "Humour" --write
inductor registry merge "Toy" "Toys" --write
```

Without `--write` each one reports what it would do and touches nothing. Adding
a tag also accepts it: every recording still proposing it gets it, which is what
`adjudicate --apply` would have done with an approval. Removing one puts it back
in `provenance.proposed_tags` with the reason rather than deleting the evidence.

For more than one change, write them down and apply them together:

```yaml
apiVersion: inductor/v1
kind: TagBulkUpdate
changes:
  - tag: Humour
    action: Add
    description: Comedy is part of the intent; the recording is meant to be funny.
  - tag: humor
    action: Merge
    target: Humour
  - tag: Abstract
    action: Remove
    why: a placeholder applied to 284 files, which tells a listener nothing
  - tag: Toys
    action: Update
    description: Sex toys used on or by the listener or the speaker.
```

```sh
inductor registry bulk changes.yaml --write
```

Changes apply in the order written, so a later one may rely on an earlier one —
the `Merge` above needs the `Add` above it. The whole file is planned first and
refused as a unit if any line is wrong, because a half-applied vocabulary change
leaves the registry, the items and the maps disagreeing with each other and
nothing saying so.

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
