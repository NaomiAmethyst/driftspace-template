# state/ — expensive, and not disposable

Produced by the pipeline, like `cache/`, and that is where the resemblance ends.
The line between the two is not how the files were made but what it would take
to make them again.

```
decisions/     tag maps and rulings: what a person decided, and why
transcripts/   what was heard, keyed by the audio's fingerprint
enrichment/    what the models made of it, keyed by the transcript's
sync/          the sync endpoint's store, if you run one
```

**Do not delete this directory.** A library of a few thousand recordings is
GPU-days of transcription, a few hundred dollars of model calls, and a set of
editorial judgements nobody can reconstruct — including the person who made
them.

## Why the keys matter

Transcripts are keyed by a fingerprint of the **audio payload with ID3
excluded**, so re-tagging a file, renaming it, or moving it never re-transcribes
it. Enrichment is keyed by the transcript's own hash, so re-running the analysis
over an unchanged transcript costs nothing.

That is also what makes this directory survive a rebuild. Delete `content/`,
re-import from `sources/`, and the run picks every transcript and every analysis
back up out of here. Delete this, and the same rebuild starts from silence.

## sync/

Only there if you run `hypnotica serve --sync state/sync`. It holds what your
devices have posted to each other and any share you have published, and it is
the one directory here that **nothing on this machine can read**: the blobs are
encrypted in the browser under a key the server is never given.

```
sync/g/<group>/s/     one library's devices, their encrypted slots
sync/pf/<id>.json     a published share: read-only, its own key
sync/pr/<id>.json     a pairing, five minutes and one use
```

`hypnotica sync --dir state/sync` lists what is stored and `--rm <id>` removes
a group or a share. That is the only safe way to delete from here: a file you
cannot read is a file whose cost you cannot judge.

It is not a backup of what the browsers hold, and it is not a way back in.
Losing every device loses the key and leaves the ciphertext inert — the export
file is the recovery path, the same one as for a library that never turned
sync on. Back this directory up if you like; back up the export file either
way.

## decisions/

The only part of this directory a person writes by hand, and the part worth
reading. See [`decisions/README.md`](decisions/README.md).

## transcripts/ and enrichment/

Machine-written JSON, one file per key. Nothing here is meant to be edited: fix
a bad transcript by re-running the stage, not by editing the blob.

They are large — a few thousand recordings runs to hundreds of megabytes of
JSON, which is a lot of git history for files nobody reads. Whether `state/`
belongs in git is a judgement call; `.gitignore` carries commented lines for it
either way. Whatever you decide, **back this directory up**.

## Rebuilding without it

If you have lost it, you have not lost the library — `content/` is still the
library. You have lost the ability to rebuild the library cheaply. A re-run will
transcribe and enrich everything from scratch, and `--overwrite` is what decides
whether the second pass is allowed to replace the writing from the first.
