#!/usr/bin/env python3
"""Pull a creator's own bio and photograph out of a mirror of their site.

The other two examples here are about recordings. This one is about the people
who made them, and it is the same argument one level up: a creator page will
happily carry a synopsis a model wrote and an avatar a renderer drew, and a
mirror of their site has their own words and their own face sitting in it. The
invented version is not bad. It is just not theirs.

This writes `kind: Author` source records, one per creator, from a list saying
which mirror directory belongs to whom. `inductor authors --only-adopt` then
puts them onto pages that already exist -- replacing what a model made, and
stopping at anything a person wrote.

  example_author_pages.py --root ~/mirrors --map mirrors.json --out sources/authors.yaml

where `mirrors.json` is a list of [directory, creator id, display name]:

  [["somecreator", "some-creator", "Some Creator"],
   ["another",     "another-one",  "Another One"]]

What it refuses to do matters more than what it does:

- **A picture must be on the creator's own domain.** One mirror's `og:image`
  is an Unsplash stock photo of a dog; the creator's actual face is the site
  icon. Taking og:image on faith would have put a stock photo on their page
  and marked it as them. Third-party hosts are rejected outright, and the file
  has to exist in the mirror -- nothing here fetches anything.
- **A login wall is not a bio.** "Just log in with your Patreon account to
  unlock this page" extracts exactly like prose does. So does a cookie notice.
- **Too short is not a bio either.** A tagline is not what the page needs, and
  a bad short one displaces a synopsis that at least described the catalogue.

Needs PyYAML and BeautifulSoup. Writes nothing without --out.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import warnings
from pathlib import Path
from urllib.parse import urlsplit, unquote

import yaml
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from PIL import Image

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


class Block(str):
    """A string to emit as a YAML literal block, so bios stay readable."""


yaml.add_representer(
    Block, lambda d, s: d.represent_scalar("tag:yaml.org,2002:str", s, style="|"),
    Dumper=yaml.SafeDumper)

# Pages that plausibly say who somebody is. Anything may follow the keyword
# within its path segment -- one site's is `about-me-and-how-to-support` -- and
# the page itself may be `index.html`, `<slug>.html`, or extensionless, because
# that is how wget writes whatever the URL was.
ABOUT = re.compile(
    r"/(about|bio|biography|profile|who[-_ ]?i[-_ ]?am)[^/]*"
    r"(/(index)?(\.html?)?)?$", re.I)
# A dated path is a blog post, whatever it is called. `meet` was a keyword here
# until it matched a listener's story about meeting their mistress and a page
# selling live DMs, in two different mirrors -- neither of them a biography,
# both of them first-person prose about the creator.
DATED = re.compile(r"/(19|20)\d{2}/\d{1,2}/")
# ...but `about-bg-5.jpg` is a background image, not a page.
NOT_A_PAGE = re.compile(r"\.(jpe?g|png|gif|webp|svg|css|js|json|xml|ico|mp3|m4a|mp4|pdf)$", re.I)
# Furniture that reads like prose and is not.
CHROME = re.compile(
    r"like loading|share this|posted in|tagged with|leave a (reply|comment)"
    r"|continue reading|read more|previous post|next post|proudly powered"
    r"|copyright|all rights reserved|cookie|privacy policy|terms of (use|service)"
    r"|^\s*(home|menu|search|cart|checkout|login|sign up)\s*$", re.I)
# A shop window. Prices, running times and "add to cart" are what a homepage
# is full of, and it all extracts as prose: one creator's "bio" came out as
# nine products and their prices, another's as the teaser for a single file.
SHOPFRONT = re.compile(
    r"add to cart|\$\s?\d|\u00a3\s?\d|\u20ac\s?\d|session length|running time"
    r"|buy now|add to basket|read more|\bmp3\b.{0,20}\$|now live|on sale", re.I)
# A page that is a door, not a room.
LOCKED = re.compile(
    r"log ?in with your|unlock this page|become a (patron|member)|subscribe to (see|read|unlock)"
    r"|this (content|page) is (for|only)|members only|password protected"
    r"|enable javascript|verify you are human|age verification", re.I)
# Image hosts that are never the creator.
STOCK = re.compile(
    r"(^|\.)(unsplash|pexels|pixabay|shutterstock|gettyimages|istockphoto"
    r"|gravatar|googleusercontent|fbcdn|placehold(er)?|via\.placeholder)\.", re.I)
PICTURE = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"}
# Pictures that are on the creator's own domain and still are not the creator:
# the icons a theme ships, the badge of whatever service they link to, and the
# favicon, which is sixteen pixels of something.
FURNITURE = re.compile(
    r"/(media-)?icons?/|/badges?/|favicon|/sprites?/|/emoji|/flags?/"
    r"|(^|/)(patreon|ko-?fi|paypal|twitter|bluesky|discord|reddit|youtube|instagram"
    r"|tumblr|mastodon|fetlife|throne|amazon|rss|cart|logo-?(twitter|x|fb))[-_.]", re.I)
# Below this a picture is furniture whatever it is called. The creator pages
# render at a few hundred pixels, and an avatar smaller than its frame looks
# worse than no avatar.
SMALLEST = 200
SOCIAL = {
    "twitter.com": "twitter", "x.com": "twitter", "bsky.app": "bluesky",
    "patreon.com": "patreon", "ko-fi.com": "kofi", "soundgasm.net": "soundgasm",
    "reddit.com": "reddit", "youtube.com": "youtube", "instagram.com": "instagram",
    "tumblr.com": "tumblr", "mastodon.social": "mastodon", "fetlife.com": "fetlife",
    "linktr.ee": "links", "throne.com": "wishlist", "amazon.com": "wishlist",
}


def soup_of(path: Path):
    try:
        return BeautifulSoup(path.read_text(encoding="utf-8", errors="replace"), "lxml")
    except Exception:
        return None


# Narrowest first. `select_one` with a comma-separated list does *not* honour
# the order they are written in -- it returns whichever element comes first in
# the document -- so a page whose <article> wraps both the bio and a catalogue
# yielded the catalogue too, ran past the length ceiling, and was thrown away
# whole. Ask for each in turn instead.
CONTENT = (".field--name-body", ".entry-content", ".post-content", ".node__content",
           "article .content", "main article", "article", "main", "#content")


def content_node(soup):
    for sel in CONTENT:
        node = soup.select_one(sel)
        if node is not None:
            return node
    return soup.body


def prose(node) -> str:
    """The readable paragraphs of a page, with the furniture taken out."""
    if node is None:
        return ""
    for bad in node(["script", "style", "form", "nav", "footer", "header", "aside"]):
        bad.decompose()
    parts: list[str] = []
    for p in node.find_all(["p", "li"]):
        if p.find(["p", "li"]):
            continue
        t = re.sub(r"\s+", " ", p.get_text(" ", strip=True)).strip()
        if len(t) < 25 or CHROME.search(t) or t in parts:
            continue
        parts.append(t)
    return "\n\n".join(parts)


def introduces(text: str, name: str) -> bool:
    """Does somebody say, in this text, that they are the creator -- by name?

    Required only of a homepage. A weaker test does not survive contact with
    this material: "I am redefining you", from the write-up of one session,
    passes any check for a first-person introduction, and the write-up then
    becomes the creator's biography. Wanting the name next to the pronoun is
    what separates "I am Goddess Kasha" from "I am the primary focus of your
    existence".
    """
    words = [w for w in re.split(r"[^A-Za-z0-9]+", name) if len(w) > 2]
    if not words:
        return False
    lead = r"(?:i am|i'm|i\u2019m|my name is|this is)\s+(?:\w+\s+){0,2}"
    return any(re.search(lead + re.escape(w) + r"\b", text, re.I) for w in words)


def bio_of(path: Path, *, is_about: bool, name: str = "") -> str:
    """The creator's own words about themselves, or nothing.

    A page called `about` is about them, and whatever prose it holds is taken.
    A homepage is not: it is a shop window, and its prose is prices, running
    times and the teaser for whatever came out last. Four of five homepages
    tried this way produced a catalogue listing that reads exactly like a bio
    and is not one, so a homepage has to earn it -- no shopfront language, and
    somebody actually introducing themselves.
    """
    s = soup_of(path)
    if s is None:
        return ""
    node = content_node(s)
    text = prose(node)
    if not text or LOCKED.search(text):
        return ""
    # A tagline is not a bio, and an entire catalogue page is not one either.
    if not 160 <= len(text) <= 6000:
        return ""
    if not is_about and (SHOPFRONT.search(text) or not introduces(text, name)):
        return ""
    return text


def paragraphs(text: str) -> str:
    """Plain text back into the markup a description is expected to hold.

    `description` is rendered as HTML, and nothing downstream turns a blank
    line into a paragraph break -- so text that reads perfectly in the YAML
    arrives on the page as one unbroken slab. The tags came off during
    extraction to get at the words; they go back on as paragraphs, and the
    words are escaped on the way because the entities were decoded too.
    """
    out = []
    for para in text.split("\n\n"):
        para = para.strip()
        if para:
            out.append("<p>" + html.escape(para, quote=False) + "</p>")
    return "\n".join(out) + "\n"


def local(root: Path, url: str) -> Path | None:
    """Where a URL's file sits in the mirror, if the mirror has it."""
    u = urlsplit(html.unescape(url))
    if not u.netloc:
        return None
    rel = unquote(u.netloc + u.path)
    for candidate in (rel, rel.rstrip("/") + "/index.html"):
        p = root / candidate
        if p.is_file():
            return p
    return None


def picture_of(root: Path, path: Path, host: str) -> tuple[str, str] | None:
    """The creator's own photograph, as (url, local path), or nothing.

    Ordered by how likely each is to be a person rather than decoration: a
    site's own icon is chosen deliberately and is usually a face or a logo,
    where og:image is whatever the theme grabbed.
    """
    s = soup_of(path)
    if s is None:
        return None
    wanted: list[str] = []
    for link in s.find_all("link", href=True):
        rel = " ".join(link.get("rel") or []).lower()
        if "icon" in rel and "mask" not in rel:
            wanted.append(link["href"])
    for meta in s.find_all("meta", content=True):
        if (meta.get("property") or meta.get("name") or "").lower() in (
                "og:image", "twitter:image", "og:image:secure_url"):
            wanted.append(meta["content"])
    wanted += [i["src"] for i in s.find_all("img", src=True)]
    for url in wanted:
        u = urlsplit(html.unescape(url))
        if not u.netloc or STOCK.search(u.netloc):
            continue
        # Their own domain, or nothing: a picture served from somebody else's
        # host is somebody else's picture until proven otherwise.
        if host not in u.netloc and u.netloc not in host:
            continue
        path_part = unquote(u.path)
        if Path(path_part).suffix.lower() not in PICTURE:
            continue
        if FURNITURE.search(path_part):
            continue
        on_disk = local(root, url)
        if on_disk is None or on_disk.stat().st_size <= 4096:
            continue
        # The only thing that actually settles whether a file is a picture of
        # somebody or a piece of chrome is how big it is. A favicon named like
        # a portrait is still a favicon.
        try:
            with Image.open(on_disk) as im:
                w, h = im.size
        except Exception:
            continue
        if min(w, h) < SMALLEST or max(w, h) > 6 * min(w, h):
            continue
        # Not resolve(): these mirrors are reached through an alias that
        # survives the volume being re-provisioned, and resolving walks back to
        # the raw CSI path, which does not. One file under two mount spellings
        # defeats every string-keyed match downstream.
        return url.split("?")[0], str(on_disk)
    return None


def links_of(path: Path, host: str) -> dict[str, str]:
    s = soup_of(path)
    if s is None:
        return {}
    out: dict[str, str] = {}
    for a in s.find_all("a", href=True):
        u = urlsplit(html.unescape(a["href"]))
        netloc = u.netloc.lower().removeprefix("www.")
        if netloc in SOCIAL and SOCIAL[netloc] not in out:
            out[SOCIAL[netloc]] = f"{u.scheme or 'https'}://{u.netloc}{u.path}".rstrip("/")
    return out


def candidates(root: Path) -> tuple[list[Path], list[Path]]:
    """About-ish pages, then the site's front door as a fallback."""
    about, home = [], []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = "/" + str(p.relative_to(root))
        bare = rel.split("?")[0]
        if NOT_A_PAGE.search(bare) or DATED.search(bare):
            continue
        if ABOUT.search(bare):
            about.append(p)
        elif p.name in ("index.html", "index.htm") and rel.count("/") <= 2:
            home.append(p)
    return sorted(about), sorted(home)


def host_of(root: Path) -> str:
    """The mirror's own domain, taken from its top directory."""
    for child in sorted(root.iterdir()):
        if child.is_dir() and "." in child.name:
            return child.name.lower().removeprefix("www.")
    return ""


def study(root: Path, name: str, ident: str) -> dict:
    host = host_of(root)
    about, home = candidates(root)
    found: dict = {"apiVersion": "inductor/v1", "kind": "Author", "name": name, "id": ident}
    where: dict = {}
    for p in about + home:
        text = bio_of(p, is_about=p in about, name=name)
        if text:
            found["description"] = Block(paragraphs(text))
            where["bio"] = str(p)
            break
    for p in about + home:
        got = picture_of(root, p, host)
        if got:
            found["image"] = got[1]
            where["image"] = got[0]
            break
    for p in about + home:
        got = links_of(p, host)
        if got:
            found["links"] = got
            break
    if host:
        found["url"] = f"https://{host}"
    found["provenance"] = {"metadata_source": f"mirror of {host}" if host else "site mirror"}
    found["_where"] = where
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True, type=Path, help="directory holding the mirrors")
    ap.add_argument("--map", required=True, type=Path,
                    help="JSON list of [mirror-dir, creator-id, display name]")
    ap.add_argument("--skip-image", action="append", default=[], metavar="ID",
                    help="creator whose picture candidate a person has looked at and "
                         "rejected (repeatable). No heuristic tells a product photo "
                         "from a portrait; a pair of eyes does")
    ap.add_argument("--out", type=Path, help="write source records here; without it, report only")
    a = ap.parse_args()

    rows = json.loads(a.map.read_text())
    records, empty = [], []
    for mirror, ident, name in rows:
        root = a.root / mirror
        if not root.is_dir():
            empty.append((mirror, "no such mirror"))
            continue
        r = study(root, name, ident)
        where = r.pop("_where")
        if ident in a.skip_image and "image" in r:
            r.pop("image")
            where.pop("image", None)
            print(f"{ident:<26} picture rejected by hand")
        if "description" not in r and "image" not in r:
            empty.append((mirror, "nothing usable"))
            continue
        records.append(r)
        bits = []
        if "description" in r:
            bits.append(f"bio {len(r['description'])}c")
        if "image" in r:
            bits.append("picture")
        if "links" in r:
            bits.append(f"{len(r['links'])} links")
        print(f"{ident:<26} {', '.join(bits)}")
        for k, v in where.items():
            print(f"      {k}: {v}")

    print(f"\n{len(records)} creator(s) with something to adopt, "
          f"{len(empty)} without")
    for m, why in empty:
        print(f"    {m}: {why}")
    if not a.out:
        print("\n(nothing written; pass --out to write the source records)")
        return 0
    a.out.parent.mkdir(parents=True, exist_ok=True)
    with a.out.open("w", encoding="utf-8") as fh:
        yaml.safe_dump_all(records, fh, sort_keys=False, allow_unicode=True,
                           default_flow_style=False, width=100)
    print(f"\nwrote {len(records)} record(s) to {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
