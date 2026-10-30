# fineprint

**`git log` for what AI companies quietly changed.**

fineprint snapshots the public pricing, rate-limit, usage-policy, terms, privacy,
model-deprecation and changelog pages of AI vendors, normalizes each one to stable
markdown, and commits it. The git history *is* the archive: every commit is a dated,
reviewable diff. A local LLM writes one plain-English line per diff, and every line
links the raw diff, so you never have to trust the model.

- `snapshots/<vendor>/<page>.md`: the current text of each page
- `git log -p -- snapshots/openai/usage-policies.md`: its full history
- `site/`: a static timeline per vendor, plus `site/feed.xml` (RSS)
- `data/changes.jsonl`: one record per change (date, page, summary, +/- lines, diff path)

## What is watched

46 public, logged-out pages across 10 vendors: Anthropic, OpenAI, Google Gemini, xAI,
Mistral, Cursor, GitHub Copilot, Perplexity, DeepSeek and Groq. See [`pages.toml`](pages.toml).
Pages behind a login are out of scope.

## How it works

```
fetch (robots.txt-checked, >=6 s per host)  ->  normalize  ->  commit if changed
                                                           ->  summarize diff (LLM)  ->  site + RSS
```

**Normalize** (`fineprint/normalize.py`) turns HTML into markdown built for diffing, not reading.
It drops scripts, styles, nav/header/footer, forms, cookie banners, screen-reader-only text,
"was this helpful" widgets, relative timestamps ("3 hours ago") and copyright lines. It also
drops link targets and images, because URLs churn (tracking params, CDN hashes, locales).
It folds NBSP, zero-width characters and curly quotes, and decodes Cloudflare-obfuscated
emails. Absolute dates like "Last updated: May 1, 2026" are kept on purpose: a vendor
bumping that date is itself news. `tests/test_normalize.py` checks that each kind of noise
produces a byte-identical snapshot, and that real edits (a price, a quota, a removed bullet)
still produce a diff.

**Summaries** (`fineprint/summarize.py`) first cancel removed/added line pairs that differ
only in markup (e.g. `##` became `###`). If nothing else is left, the change is labelled
"Minor: formatting" with no LLM call. Otherwise the condensed diff goes to an
OpenAI-compatible endpoint (default: a local llama-server running gemma-4-12b). Lines the
model marks `Minor:` are faded on the site and left out of RSS.

**Backfill** (`python -m fineprint backfill 20260430 20261030`) rebuilds history from the
Wayback Machine. It uses the CDX API, about one capture per week per page, `id_` raw
captures, 3 s between archive.org requests, and backoff on 429/5xx. Captures that are bot
walls, JS shells, undecodable bytes, or under half the size of both neighbouring captures
are dropped. So are one-capture "blips" (A, B, A): a stale CDN copy would otherwise make two
false headlines. Every drop is listed in `data/backfill-report.json`. Live runs get the same
protection differently: a change must be seen on two consecutive fetches before it is
committed, dated to when it was first seen (`data/pending.json`). Backfilled dates mean "first seen in a weekly
sample", not the exact change time.

## Run it

```bash
pip install -r requirements.txt
python -m pytest -q tests
python -m fineprint fetch          # live snapshot of every page, one commit per changed page
python -m fineprint summarize      # needs LLAMA_API_KEY / FINEPRINT_LLM_* (or --no-llm)
python -m fineprint build          # writes site/ and site/feed.xml
```

The GitHub Actions workflow (`.github/workflows/fineprint.yml`) runs this every 6 hours.
It stays inert until the repository variable `FINEPRINT_ENABLED` is `true`.

## Caveats

- Summaries come from a 12B local model. Read the diff before you quote a summary.
- Some vendors A/B test or geo-target pages. A diff can reflect what our fetcher was shown,
  not a global change.
- When a vendor moves a page (e.g. docs.anthropic.com to platform.claude.com), the first
  snapshot after the move often has a large layout diff.
