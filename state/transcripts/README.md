# state/transcripts/ — what was heard

One JSON file per recording, keyed by a fingerprint of the **audio payload with
ID3 excluded**. Re-tagging a file, renaming it or moving it therefore never
re-transcribes it.

**Do not delete, and do not edit.** This is GPU-hours. A transcript that came out
wrong is fixed by re-running the stage against better settings, not by editing
the blob — the key is the audio, so an edited file is silently inconsistent with
what the fingerprint says is in it.

Delete `content/` and re-import, and every transcript is picked back up from
here. Delete this, and the same rebuild starts from silence.
