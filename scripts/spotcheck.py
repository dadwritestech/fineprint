"""Print a reproducible random sample of LLM summaries next to their condensed diffs.

    python scripts/spotcheck.py 30 [seed]

A human reads each pair and records a verdict in docs/spotcheck.md.
"""
import json
import random
import sys

from fineprint.summarize import CHANGES, ROOT, condense

n = int(sys.argv[1]) if len(sys.argv) > 1 else 30
seed = int(sys.argv[2]) if len(sys.argv) > 2 else 7
recs = [json.loads(l) for l in CHANGES.read_text(encoding="utf-8").splitlines() if l.strip()]
llm = [r for r in recs if r["by"] not in ("rule", "fallback")]
for i, r in enumerate(sorted(random.Random(seed).sample(llm, min(n, len(llm))), key=lambda r: r["date"]), 1):
    diff = (ROOT / "site" / r["diff"]).read_text(encoding="utf-8")
    body, pairs = condense(diff)
    print(f"=== {i}. {r['date'][:10]} {r['page']}  (+{r['added']} -{r['removed']}, {pairs} markup-only pairs)")
    print(f"SUMMARY: {r['summary']}")
    print(body[:2500] + ("\n[...]" if len(body) > 2500 else ""))
    print()
