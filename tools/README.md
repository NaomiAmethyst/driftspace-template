# tools/ — the code you write, not the code you install

Inductor and Hypnotica are installed binaries and live elsewhere. What lives here
is the throwaway code that gets *your* material into the shape Inductor expects.

```
mirrors/    one parser per source site, pack or spreadsheet
import/     one-off importers, migrations and repairs
```

Nothing here is on the critical path. A library that was imported by hand needs
neither directory; they exist because material arrives in whatever shape it
arrives in, and that shape is nobody's problem but yours.

## Two rules

**Nothing here may end up needing a change in Inductor or Hypnotica.** Those are
public tools that know nothing about any particular library. If a parser wants
something from them that they do not offer, the parser does the work.

**The source record is the interface.** Everything here exists to produce
`sources/<creator>.yaml` and then stop. Once a source record is written, the rest
of the pipeline neither knows nor cares how it got there — which is what makes
these scripts safe to delete.

## Language and dependencies

Whatever you like; these run once. The worked example in `mirrors/` is Python
with one dependency (PyYAML) because that is the shortest path to valid output.
If you reach for anything heavier, note it at the top of the file — the next
person to run it will be a year later on a different machine.
