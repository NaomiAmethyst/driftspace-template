#!/usr/bin/env python3
"""Turn a mirror of a per-recording audio host into source records.

The other worked example, `example_wordpress.py`, spends most of its length on
one problem: a site's write-ups and its audio arrive as two separate piles, and
marrying them is guesswork you have to do well. This one is the opposite case,
and it is worth reading for the contrast.

Some hosts serve one page per recording, and that page *names its own audio
file*. soundgasm is the worked instance -- `soundgasm.net/u/<user>/<Title-Slug>`
holds the title, the write-up, and a jPlayer line pointing at
`media.soundgasm.net/sounds/<sha>.m4a`. There is nothing to match: the join is a
dictionary lookup, it is exact, and every recording either resolves or plainly
does not. No normalised titles, no duration veto, no margin over a runner-up.

When a source is shaped like this, take the seam it offers and do not invent a
matcher you do not need. When it is not, read the other example.

Two things this shape does not give you, and neither is worth faking:

- **No date.** The pages carry none. Leave `date` out; `inductor` will not
  invent one either, and an entry with no date is honest where an entry with a
  made-up one is not.
- **Opaque filenames.** The audio is named by a hash, so the *only* thing that
  knows what a recording is called is the page. Lose the mirror and you have a
  folder of hashes, which is why the source record is written once and kept.

    ./example_soundgasm.py \\
        --mirror ~/mirrors/some-creator \\
        --author "Some Creator" \\
        --out ../../sources/some-creator.yaml

Needs PyYAML (`pip install pyyaml`). Writes nothing without --out.
"""
from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("this script needs PyYAML: pip install pyyaml")


class Block(str):
    """A string to emit as a YAML literal block, so descriptions stay readable."""


yaml.add_representer(
    Block, lambda d, s: d.represent_scalar("tag:yaml.org,2002:str", s, style="|"),
    Dumper=yaml.SafeDumper)

# The player embeds the audio URL in a script line. This is the seam: it is the
# page saying, unambiguously, which file it is about.
AUDIO_URL = re.compile(r'm4a:\s*"([^"]+\.(?:m4a|mp3))"')
TITLE = re.compile(r'class="jp-title"[^>]*>(.*?)</div>', re.S)
DESCRIPTION = re.compile(r'class="jp-description"[^>]*>(.*?)</div>', re.S)
TAG = re.compile(r"<[^>]+>")


def text_of(fragment: str) -> str:
    """Tags out, entities decoded, whitespace settled -- and nothing else.

    Deliberately not a sanitiser: the write-up goes into the source record as the
    creator wrote it, and deciding what it is allowed to say is a later, separate
    step that a person makes.
    """
    body = TAG.sub("", fragment)
    return "\n".join(line.strip() for line in html.unescape(body).splitlines()).strip()


def read_page(path: Path) -> dict | None:
    """One recording, as the page describes it."""
    try:
        raw = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    audio = AUDIO_URL.search(raw)
    title = TITLE.search(raw)
    if not audio or not title:
        return None
    entry = {"title": text_of(title.group(1)), "url": audio.group(1)}
    if body := DESCRIPTION.search(raw):
        if described := text_of(body.group(1)):
            entry["description"] = described
    return entry if entry["title"] else None


def local_audio(mirror: Path) -> dict[str, Path]:
    """Every audio file in the mirror, keyed by the name a page would use."""
    found = {}
    for path in mirror.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".m4a", ".mp3"}:
            found[path.name] = path
    return found


def pages(mirror: Path) -> list[Path]:
    """The per-recording pages.

    They have no extension -- wget writes the URL path as it found it -- so they
    are picked out by shape rather than by suffix: two levels under `u/`, which
    is `u/<user>/<slug>`.
    """
    out = []
    for root in mirror.rglob("u"):
        if root.is_dir():
            out += [p for p in root.glob("*/*") if p.is_file()]
    return sorted(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--mirror", required=True, type=Path,
                    help="the wget mirror: holds both the pages and the audio")
    ap.add_argument("--author", required=True, help="the creator's name, as they write it")
    ap.add_argument("--source-url", default="", help="their page, if you want it recorded")
    ap.add_argument("--out", type=Path, help="write the source file here; without it, report only")
    a = ap.parse_args()

    if not a.mirror.is_dir():
        sys.exit(f"no mirror at {a.mirror}")
    audio = local_audio(a.mirror)
    records, missing, unreadable = [], [], 0
    for page in pages(a.mirror):
        entry = read_page(page)
        if entry is None:
            unreadable += 1
            continue
        name = entry["url"].rsplit("/", 1)[-1]
        path = audio.get(name)
        if path is None:
            # The page exists and the audio does not: the mirror is incomplete,
            # which is worth saying rather than quietly emitting a record that
            # points at nothing.
            missing.append(entry["title"])
            continue
        record = {"apiVersion": "inductor/v1", "kind": "Source",
                  "audio": str(path.resolve()), "title": entry["title"],
                  "author": a.author}
        if "description" in entry:
            record["description"] = Block(entry["description"] + "\n")
        if a.source_url:
            record["source_url"] = a.source_url
        records.append(record)

    used = {r["audio"] for r in records}
    orphans = [p for p in audio.values() if str(p.resolve()) not in used]
    print(f"{len(records)} recording(s) matched their page exactly")
    if unreadable:
        print(f"{unreadable} page(s) had no player on them (index or profile pages)")
    if missing:
        print(f"{len(missing)} page(s) name audio the mirror does not have:")
        for t in missing[:10]:
            print(f"    {t}")
    if orphans:
        # A file no page claims is the shape to be suspicious of: it is either a
        # recording the creator has taken down, or a mirror fetched in two goes.
        print(f"{len(orphans)} audio file(s) no page claims:")
        for p in orphans[:10]:
            print(f"    {p.name}")
    if not records:
        sys.exit("nothing matched; check --mirror points at the directory holding u/")
    if not a.out:
        print("\n(nothing written; pass --out to write the source file)")
        return 0
    a.out.parent.mkdir(parents=True, exist_ok=True)
    with a.out.open("w", encoding="utf-8") as fh:
        yaml.safe_dump_all(records, fh, sort_keys=False, allow_unicode=True,
                           default_flow_style=False, width=100)
    print(f"\nwrote {len(records)} record(s) to {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
