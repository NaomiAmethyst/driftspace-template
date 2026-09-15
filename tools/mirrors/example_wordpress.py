#!/usr/bin/env python3
"""Turn a mirrored WordPress site plus a folder of audio into source records.

A worked example, not a general tool. Most creator sites are WordPress: one post
per release, the title in <h1 class="entry-title">, the write-up in
.entry-content, the date in the URL path. Posts are matched to audio by
normalised title, with a prefix pass for the truncated names rips leave behind
and a close-match pass for small drift.

Copy this file, name it after the source, and change what does not fit. Parsers
are disposable; the source record is the interface.

    ./example_wordpress.py \\
        --mirror ~/mirrors/some-creator \\
        --audio ~/audio/some-creator \\
        --author "Some Creator" \\
        --site https://some-creator.example \\
        --out ../../sources/some-creator.yaml

Needs PyYAML (`pip install pyyaml`). Writes nothing without --out.
"""
from __future__ import annotations

import argparse
import difflib
import re
import sys
import unicodedata
from html.parser import HTMLParser
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("this script needs PyYAML: pip install pyyaml")

AUDIO_EXT = {".mp3", ".m4a", ".m4b", ".wav", ".flac", ".ogg", ".opus"}


class Block(str):
    """A string to emit as a YAML literal block, so descriptions stay readable."""


yaml.add_representer(
    Block, lambda d, s: d.represent_scalar("tag:yaml.org,2002:str", s, style="|"),
    Dumper=yaml.SafeDumper)

# Mirror paths that are navigation rather than content.
SKIP_PATH = re.compile(
    r"/(category|tag|author|page|feed|comments|wp-content|wp-includes|wp-json"
    r"|search|amp)/|/(robots|sitemap)\.", re.I)

# Boilerplate that survives into .entry-content on most themes.
CHROME = re.compile(
    r"like loading|share this|posted in|tagged|leave a (reply|comment)"
    r"|continue reading|read more|previous post|next post|proudly powered"
    r"|subscribe|follow me|copyright|all rights reserved|add to cart", re.I)

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr"}


def norm(s: str) -> str:
    """Fold a title down to something two spellings of it can agree on."""
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    s = s.replace("&", "and")
    return re.sub(r"[^a-z0-9]+", "", s.lower())


class PostParser(HTMLParser):
    """Pull the title, the write-up paragraphs and the tags out of one post.

    Written against html.parser so this file has one dependency rather than
    three. If you are doing anything more involved, reach for BeautifulSoup.
    """

    def __init__(self, title_class: str, body_class: str) -> None:
        super().__init__(convert_charrefs=True)
        self.title_class, self.body_class = title_class, body_class
        self.title, self.paragraphs, self.tags = "", [], []
        self._stack: list[str] = []
        self._title_depth = self._body_depth = None
        self._buf: list[str] | None = None
        self._in_tag_link = False

    @staticmethod
    def _classes(attrs) -> set[str]:
        d = dict(attrs)
        return set((d.get("class") or "").split())

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            if tag == "br" and self._buf is not None:
                self._buf.append(" ")
            return
        self._stack.append(tag)
        depth, classes = len(self._stack), self._classes(attrs)

        if self._title_depth is None and not self.title:
            if self.title_class in classes or (tag == "h1" and not self.title_class):
                self._title_depth, self._buf = depth, []
                return
        if self._body_depth is None and self.body_class in classes:
            self._body_depth = depth
            return
        # Paragraphs of the write-up, and only the innermost ones.
        if self._body_depth is not None and tag in ("p", "li"):
            self._buf = []
        if dict(attrs).get("rel") == "tag":
            self._in_tag_link, self._buf = True, []

    def handle_data(self, data):
        if self._buf is not None:
            self._buf.append(data)

    def handle_endtag(self, tag):
        if tag in VOID or tag not in self._stack:
            return
        depth = len(self._stack)
        text = re.sub(r"\s+", " ", "".join(self._buf or [])).strip()

        if self._in_tag_link and tag == "a":
            if text:
                self.tags.append(text)
            self._in_tag_link, self._buf = False, None
        elif self._title_depth == depth:
            self.title, self._title_depth, self._buf = text, None, None
        elif self._body_depth is not None and tag in ("p", "li"):
            if len(text) >= 25 and not CHROME.search(text):
                self.paragraphs.append(text)
            self._buf = None
        if self._body_depth == depth:
            self._body_depth = None
        # Unwind to the matching open tag, tolerating unclosed markup.
        while self._stack:
            if self._stack.pop() == tag:
                break


def read_posts(mirror: Path, title_class: str, body_class: str):
    for path in sorted(mirror.rglob("index.htm*")):
        rel = "/" + str(path.relative_to(mirror))
        if SKIP_PATH.search(rel):
            continue
        parser = PostParser(title_class, body_class)
        try:
            parser.feed(path.read_text(encoding="utf-8", errors="replace"))
        except Exception as exc:                       # a mirror has bad files
            print(f"  ! {rel}: {exc}", file=sys.stderr)
            continue
        if not parser.title or len(parser.title) > 140 or not parser.paragraphs:
            continue
        m = re.search(r"/(\d{4})/(\d{2})/(\d{2})/", rel)
        seen, body = set(), []
        for p in parser.paragraphs:                    # themes repeat the excerpt
            if p not in seen:
                seen.add(p)
                body.append(p)
        yield {
            "title": parser.title,
            "body": body,
            "tags": sorted(set(parser.tags)),
            "date": "-".join(m.groups()) if m else "",
            "url_path": rel.rsplit("index.htm", 1)[0],
        }


def find_audio(dirs: list[Path]) -> list[Path]:
    out: list[Path] = []
    for d in dirs:
        if not d.is_dir():
            sys.exit(f"not a directory: {d}")
        out += [p for p in d.rglob("*") if p.suffix.lower() in AUDIO_EXT]
    return sorted(set(out))


def match(audio: list[Path], posts: list[dict], strip: str):
    """One post per file, at most, cheapest test first."""
    index: dict[str, dict] = {}
    for post in posts:
        key = norm(post["title"])
        if len(key) > 3:
            index.setdefault(key, post)

    matched, unmatched = [], []
    for path in audio:
        stem = re.sub(strip, "", path.stem, flags=re.I).strip(" -~_") if strip else path.stem
        key = norm(stem)
        hit = index.get(key)
        if not hit and len(key) > 8:
            # A rip truncated the name, or the site added a suffix. Only accept
            # a prefix match when exactly one post could be meant.
            near = {id(v): v for k, v in index.items()
                    if k.startswith(key) or key.startswith(k)}
            if len(near) == 1:
                hit = next(iter(near.values()))
        if not hit:
            close = difflib.get_close_matches(key, list(index), n=1, cutoff=0.9)
            if close:
                hit = index[close[0]]
        (matched.append((path, hit)) if hit else unmatched.append(path))
    return matched, unmatched


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mirror", required=True, type=Path, help="the mirrored site")
    ap.add_argument("--audio", required=True, type=Path, action="append",
                    help="folder of this creator's audio (repeatable)")
    ap.add_argument("--author", required=True, help="the creator's display name")
    ap.add_argument("--site", default="", help="site root, for source_url")
    ap.add_argument("--strip", default="",
                    help="regex of a creator name or prefix to drop from filenames")
    ap.add_argument("--title-class", default="entry-title")
    ap.add_argument("--body-class", default="entry-content")
    ap.add_argument("--out", type=Path, help="source file to write; omit for a dry run")
    args = ap.parse_args()

    posts = list(read_posts(args.mirror, args.title_class, args.body_class))
    print(f"{len(posts)} posts with a body")
    if not posts:
        print("nothing parsed: check --title-class and --body-class against the "
              "mirror's actual markup", file=sys.stderr)
        return 1

    audio = find_audio(args.audio)
    matched, unmatched = match(audio, posts, args.strip)
    print(f"{len(audio)} audio files, {len(matched)} matched, {len(unmatched)} not")
    for path in unmatched[:15]:
        print("   ", path.stem)
    if len(unmatched) > 15:
        print(f"    ... and {len(unmatched) - 15} more")

    records = []
    for path, post in matched:
        rec = {
            "apiVersion": "inductor/v1",
            "kind": "Source",
            "audio": str(path.resolve()),
            "title": post["title"],
            "author": args.author,
        }
        if post["date"]:
            rec["date"] = post["date"]
        if post["body"]:
            rec["description"] = Block("".join(f"<p>{p}</p>" for p in post["body"]) + "\n")
        if post["tags"]:
            rec["tags"] = post["tags"]      # their words; tagmap deals with them
        if args.site:
            rec["source_url"] = args.site.rstrip("/") + post["url_path"]
        records.append(rec)

    if not args.out:
        print("\ndry run; pass --out to write. First record:\n")
        if records:
            print(yaml.safe_dump(records[0], sort_keys=False,
                                 allow_unicode=True, width=100))
        return 0

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write("---\n")
            yaml.safe_dump(rec, fh, sort_keys=False, allow_unicode=True, width=100)
    print(f"\nwrote {len(records)} records to {args.out}")
    print("now run: inductor check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
