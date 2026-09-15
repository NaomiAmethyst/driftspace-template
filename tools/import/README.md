# tools/import/ — one-off importers, migrations and repairs

Scripts that ran once, against this library, to move something from one shape to
another. Unlike `mirrors/`, these touch `content/` and `state/` directly, which
is why they get their own directory and a warning.

Typical inhabitants:

- An importer for material that came from somewhere a parser could not reach —
  a spreadsheet, another catalogue, a previous attempt at this.
- A migration, when a convention changes and several hundred files have to
  follow it.
- A repair, when something got in wrong and `inductor` has no command for the
  specific mess.

## Before writing one, check there is not a command already

Inductor has commands for most of what people reach for a script to do, and they
keep a record of what they did:

| | |
|---|---|
| `retag`, `fold` | change or merge tags across the library |
| `retitle` | titles and the ids derived from them |
| `paths --write` | normalise absolute paths to relative ones |
| `attribute --write` | fill in `provenance.generated` on older entries |
| `authors` | creator records and pages |
| `duplicates` | recordings imported twice |
| `orphans` | transcripts and pages nothing refers to |
| `migrate` | move a tree onto the current layout |

Reach for a script only when none of those fits.

## If you do write one

- **Dry-run first, and make that the default.** Print what would change, count
  it, and require a flag to write. A run that touches every item in the library
  is not a thing to get right on the second attempt.
- **Never drop `provenance:`.** It is the record of where a value came from and
  whether a machine wrote it. Rebuilding an item from its source record without
  carrying provenance forward is how one library lost the summary and spoilers
  of 381 live items in a single run.
- **Commit first** if the library is in git, so the diff is the undo.
- **Write down what it was for**, at the top of the file, in a sentence. A year
  from now the filename will not be enough.
