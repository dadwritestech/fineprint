# Summary spot-check (v0)

The sample is 30 LLM summaries drawn with a fixed seed from the 397 changes in `data/changes.jsonl`. Regenerate it with:

    PYTHONPATH=. python scripts/spotcheck.py 30 7

Each summary was read against its diff. When the condensed diff shown was truncated, I checked the full diff in `site/diffs/`.
The model was gemma-4-12b on the local llama-server, with thinking off, temperature 0.1 and max_tokens 90.

## Result

**27 / 30 factually accurate. There were no invented numbers in the sample.** The 3 problems:

| # | Page | Problem |
|---|---|---|
| 11 | anthropic/rate-limits 2026-06-06 | It added "(deprecated)" labels but was tagged `Minor:`. The content is right, but the severity is arguably wrong. |
| 13 | xai/terms-of-service 2026-07-01 | It mentions only the new effective date and omits the substantive scope edits in the same diff. This is misleading by omission. |
| 14 | anthropic/model-deprecations 2026-07-03 | It reports table rows as "added", but they were missing from the previous capture because that table was truncated. The change is a capture artifact, not a vendor change. The summary is also cut off mid-sentence because of max_tokens. |

Weaker but counted as accurate:
- #7 is vague ("added descriptions for new models").
- #26 and #30 each omit one secondary change: a Whisper file-size edit, and the Haiku 5.5 rows.
- #5 summarises a trivial wording change; the diff also contains glued tab labels ("ProPro+Ultra"), which is a normalizer artifact.
- #3's snapshot duplicates the Gemini 3.5 Flash rows; that is a normalizer artifact, and the summary itself is fine.

Two items needed the full diff:
- #19 (Mistral Large "$0.5 / $1.5") looked like a hallucination in the truncated view. The full diff shows `$2 /M in, $6 /M out` → `$0.5 /M in, $1.5 /M out`, so the summary is correct.
- #8 (Gemini pricing 2026-05-29) checked out: a preview model was removed, two image models were renamed to stable, and embedding prices were added.

## Known error outside the sample

`2026-09-03 anthropic/pricing`: the summary reads "Added Fable 5.1 at $0.25 / MTok". In the diff, $0.25 is Fable 5.1's **cache-read** price, not its base price. Line-level diffing paired `$12.50` with `$0.25`, and the model read that as a headline price. The same summary's "legacy pricing $10/$50" refers to Fable 5 moving into a legacy section.

The weakness here is that pricing cards render as one value per line, so diff alignment loses the row label. Treat price numbers in summaries as pointers to the diff, not as facts. That is why every RSS item links the raw diff.

## Honest read

- With a sample of 30, the true accuracy rate is roughly 75–97% (95% interval). "About 9 in 10" is the right claim; "always right" is not.
- The commonest failure is omission, not invention. Diffs often hold several changes, and a single line keeps the first one or two.
- Capture artifacts (truncated Wayback pages) can still reach the feed. The dip/blip filters catch most of them, but not a table that is missing in one capture and then stays restored.
- Next steps: raise max_tokens to about 140 so long summaries aren't cut, and give price-card pages a row-aware normalizer.
