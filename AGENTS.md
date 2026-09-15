# AGENTS.md

The working notes for this library live in [`CLAUDE.md`](CLAUDE.md). They are not
Claude-specific — read that file, then the `README.md` in whichever directory you
are about to touch.

The short version:

- `content/` is the library and the only thing that matters long-term. `cache/`
  is disposable. `state/` is neither: expensive to rebuild, impossible to
  reconstruct.
- Tags come from `content/tags.yaml` and nowhere else. Propose new ones; do not
  add them.
- Change the library through `inductor` commands rather than by hand-editing
  hundreds of YAML files.
- Do not commit audio, and do not publish anything without being asked to.
