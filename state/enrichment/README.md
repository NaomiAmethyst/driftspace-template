# state/enrichment/ — what the models made of it

One JSON file per recording, keyed by the **transcript's** hash rather than the
audio's, so re-running analysis over an unchanged transcript costs nothing.

Each holds the analysis pass (what the recording contains, with the sentences
cited for every claim) and the review pass (the entry written from only those
cited passages). The split is what keeps quotes real: the reviewer sees the
evidence, not the recording.

**Do not delete, and do not edit.** This is the part of the library that costs
money. Re-run the stage with `--redo-analysis` if an entry needs doing again.
