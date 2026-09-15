# cache/ — disposable

Everything under here can be deleted at any time. Nothing in it is a record of
anything; it exists so a re-run does not repeat work the filesystem can already
answer for. Deleting it costs time on the next run and nothing else.

If you are wondering whether a file belongs here or in `state/`, ask what it
would take to make it again. A measurement is a decode away. A transcript is
GPU-hours and a tag ruling is a judgement nobody can reconstruct — those go in
`state/`.

```
inductor/      Inductor's working directory (paths.cache in inductor.yaml)
  acoustic/      acoustic fingerprints, one per recording
  analysis/      staged model analysis in flight
  remote-out/    results coming back from a remote transcription worker
  stt-stage/     audio staged for the transcription worker
  voiceprints/   speaker embeddings
hypnotica/     whatever a site build keeps between runs
```

Inductor also keeps two indexes at the top of `cache/inductor/`, both keyed on
what the filesystem already knows — a fingerprint index (device and inode,
checked against size and mtime) and an item index (size and mtime per item
file). They are why a warm full-library plan takes seconds and a cold one takes
a minute.

Two things live here that are *briefly* worth keeping: the batch journals, which
hold the IDs of review batches submitted to OpenRouter, and anything staged for
a worker mid-run. Do not clear the cache while a run is in flight — a submitted
batch has no cancel endpoint, and losing its ID means paying for it twice. Wait
for the run to finish, or note the batch ID and use `ingest --recover`.

This directory is in `.gitignore`; the `.gitkeep` files are committed so the
layout survives a clone.
