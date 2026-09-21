# media/ — audio and artwork, where the site can serve them

```
audio/<creator>/<title>.mp3      what the item's audio: points at
cover/<creator>/<id>.png         per-item artwork
cover/<creator>/_author.png      the creator's page image
video/<creator>/<title>.mp4      the container a recording arrived in, if any
```

`inductor run` fills this in. By default the audio files are **symlinks** into
wherever the originals live — `media.mode` in `inductor.yaml` also takes
`hardlink` and `copy`. Symlinks mean one copy of the audio on disk and a library
that depends on the originals staying put; copies mean a directory that stands
on its own at twice the size. For a few thousand recordings that difference is
hundreds of gigabytes, so the default is symlink.

Nothing here modifies the source audio. Transcoding, where `media.transcode`
asks for it, writes a new file here and leaves the original alone.

## After moving the library

A link that points *out* of the library is absolute, because that is where the
file is. A link that points *inside* it — a cover standing in for another
cover, most often — is relative, so the whole directory can be moved or cloned
and still find itself.

Move a library built before that was true and the second kind all break at
once. Nothing errors: `inductor` does not read them, and the only thing that
does is the site build, which reports artwork it cannot find and carries on.

```sh
inductor paths            # what it would relink
inductor paths --write
```

It works out where a dead link meant by the tail of its own target —
`media/cover/<creator>/<stem>.png` names the same file under the new root as it
did under the old one — and leaves anything it cannot account for exactly as it
is, listed under `dangling`. Read that list: a link whose target never existed
is a different problem from a link whose library moved.

`video:` is the container a recording arrived in, kept beside the `audio:`
extracted from it. Only the item page shows it; the player, the queue and
anything saved offline take the audio track.

## This directory is not in git

`.gitignore` excludes the contents; the `.gitkeep` files are committed so the
layout survives a clone. That is deliberate, and it is not a decision you should
reverse without thinking about it:

- A few thousand recordings is a few hundred gigabytes.
- Git stores every version of every binary forever, and cannot delta them.
- No forge will take it, and a repository that large is slow to do anything with
  even locally.

What to do instead, roughly in order of how much trouble it is:

- **Leave it out.** The contents are symlinks; the real files are wherever they
  already were. Back *that* up the way you back up anything else — `rsync`,
  `restic`, `borg`, a second disk. This is the default and it is usually right.
- **[git-annex](https://git-annex.branchable.com/)**, which keeps file contents
  outside git and filenames inside it. The closest fit to the problem: it is
  built for exactly this, and it tracks which drive holds which copy.
- **[Git LFS](https://git-lfs.com/)**, if you are pushing to a forge that offers
  it and can live with the quotas.
- **[Syncthing](https://syncthing.net/)** or similar, running alongside the git
  repository rather than inside it.

The YAML in `content/` is what is worth versioning. It is small, it is the
expensive part to rebuild, and its history is a record of what was decided about
each recording.

## Artwork

Covers come from a local [ComfyUI](https://github.com/comfyanonymous/ComfyUI),
and are **off by default** — `enrich.covers` in `inductor.yaml`. Turn them on
when you have one running, or generate them later:

```sh
inductor cover-prompts        # write the prompts into the items
inductor artwork              # render them
```

Each item carries `cover_prompts:` in both styles — `tagged` for SDXL-family
renderers, `natural` for Flux/SD3-family ones — so changing renderer is a flag
rather than another pass over the library.
