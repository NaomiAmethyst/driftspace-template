# cache/inductor/ — Inductor's working directory

`paths.cache` in `inductor.yaml`. Disposable in full; see [`../README.md`](../README.md).

| | |
|---|---|
| `acoustic/` | acoustic fingerprints, one per recording |
| `analysis/` | staged model analysis in flight |
| `remote-out/` | results coming back from a remote transcription worker |
| `stt-stage/` | audio staged for the transcription worker |
| `voiceprints/` | speaker embeddings |
| `batches/` | OpenRouter batch journals — see the warning below |
| `fingerprints.json` | audio fingerprints, keyed by device and inode |
| `item-index.json` | size and mtime per item file |

Inductor creates whatever it needs; the empty directories here are just the
layout, kept so a fresh clone looks like a working one.

**Do not clear this while a run is in flight.** A submitted review batch has no
cancel endpoint, and its ID lives in `batches/`. Losing the ID means paying for
the same reviews twice — `ingest --recover <batch-id>` is the way back if you
still have it.
