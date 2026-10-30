"""Real-world noise audit over the raw cache.

For each page: how many sampled captures, how many distinct normalized versions,
and the smallest diffs between consecutive versions (tiny diffs are where noise hides).
A page whose versions ~= captures is suspicious: something unstable is leaking through.
"""
import difflib
import sys
from pathlib import Path

from fineprint.fetch import CACHE, load_pages
from fineprint.normalize import html_to_markdown
from fineprint.store import looks_broken

show = int(sys.argv[1]) if len(sys.argv) > 1 else 2
tot_caps = tot_versions = 0
for p in load_pages():
    files = sorted((CACHE / p["vendor"] / p["slug"]).glob("wb-*.html"))
    if not files:
        print(f"{p['vendor']}/{p['slug']:<26} no captures")
        continue
    prev, versions, small = None, 0, []
    for f in files:
        md = html_to_markdown(f.read_text(encoding="utf-8"), p.get("select"))
        if looks_broken(md):
            continue
        if md != prev:
            versions += 1
            if prev is not None:
                ch = [l for l in difflib.unified_diff(prev.splitlines(), md.splitlines(), lineterm="", n=0)
                      if l[:1] in "+-" and l[:3] not in ("+++", "---")]
                small.append((len(ch), f.stem[3:11], ch[:4]))
            prev = md
    tot_caps += len(files)
    tot_versions += versions
    flag = "  <-- check" if versions > 0.6 * len(files) and len(files) > 4 else ""
    print(f"{p['vendor']}/{p['slug']:<26} captures {len(files):>3}  versions {versions:>3}{flag}")
    for n, day, ch in sorted(small)[:show]:
        print(f"      {day} {n:>3} lines: " + " || ".join(c[:80] for c in ch))
print(f"TOTAL captures {tot_caps}, distinct versions {tot_versions}")
