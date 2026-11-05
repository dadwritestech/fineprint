# Contributing to fineprint

## Setup

```bash
git clone https://github.com/dadwritestech/fineprint && cd fineprint
pip install -r requirements.txt
python -m pytest -q tests
```

## Watch a new page

1. Add an entry to [`pages.toml`](pages.toml). Copy a neighbour: `vendor`, `slug`, `kind`, `url`, and an optional CSS `select` that narrows the page to its main content.
2. The page must be public and work logged out. It must also be allowed by the site's robots.txt (`python -m fineprint fetch` checks this and skips disallowed pages).
3. Run `python -m fineprint fetch --only <vendor>/<slug>` twice, a few minutes apart, then run `python scripts/audit_noise.py`. A page that gives a new version on every fetch has noise (timestamps, rotating banners or A/B blocks). Fix it in `fineprint/normalize.py` and add a test to `tests/test_normalize.py`, so that noise never produces a diff. Don't commit the snapshots from these test fetches.
4. Open a PR with the `pages.toml` change. Leave out the snapshot; CI takes the first one.

## Report a wrong summary

Open an issue with the diff link. Summaries come from a small local model, and the diff is always the source of truth. Fixes to `data/changes.jsonl` are welcome as PRs: change the `summary`, keep everything else, and set `"by": "human"`.

## Ground rules

- Only public, logged-out pages. No logins, no paywalls, no evading bot protection.
- Be polite to hosts: keep the 6-second per-host gap in `fineprint/fetch.py`.
- Never commit API keys. The LLM key is read from the environment only.
