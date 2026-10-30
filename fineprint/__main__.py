"""fineprint CLI.

  python -m fineprint fetch                 # live run (what CI does every 6h)
  python -m fineprint backfill 20260430 20261030 [--every-days 7]
  python -m fineprint summarize             # one-line LLM summary per diff
  python -m fineprint build                 # static site + RSS into site/
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import statistics
import sys
import time

from . import fetch, store
from .normalize import html_to_markdown, snapshot_text


def log(*a) -> None:
    print(*a, flush=True)


def _select(pages: list[dict], only: list[str] | None) -> list[dict]:
    if not only:
        return pages
    return [p for p in pages if p["vendor"] in only or f"{p['vendor']}/{p['slug']}" in only]


def cmd_fetch(args) -> int:
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    stamp = "live-" + now.strftime("%Y%m%d%H%M%S")
    changed, problems = 0, []
    for page in _select(fetch.load_pages(), args.only):
        pid = f"{page['vendor']}/{page['slug']}"
        ok, why = fetch.robots_allows(page["url"])
        if not ok:
            problems.append((pid, why))
            continue
        try:
            status, html = fetch.fetch_live(page["url"])
        except Exception as e:  # noqa: BLE001
            problems.append((pid, f"fetch error: {e!r}"[:200]))
            continue
        if status != 200:
            problems.append((pid, f"HTTP {status}"))
            continue
        fetch.store_cache(page, stamp, html)
        text = snapshot_text(page, html)
        bad = store.looks_broken(html_to_markdown(html, page.get("select")))
        if bad:
            problems.append((pid, bad))
            continue
        sha = store.commit_snapshot(page, text, now.isoformat(), f"live fetch {stamp[5:]}")
        if sha:
            changed += 1
            log(f"changed  {pid}  {sha[:8]}")
    for pid, why in problems:
        log(f"skipped  {pid}: {why}")
    log(f"{changed} page(s) changed, {len(problems)} skipped")
    return 0


def _weekly(caps: list[dict], every_days: int) -> list[dict]:
    """First capture in each N-day bucket, plus the newest capture."""
    picked, last_day = [], None
    for c in caps:
        day = dt.datetime.strptime(c["timestamp"][:8], "%Y%m%d").date()
        if last_day is None or (day - last_day).days >= every_days:
            picked.append(c)
            last_day = day
    if caps and caps[-1] is not picked[-1]:
        picked.append(caps[-1])
    return picked


def cmd_backfill(args) -> int:
    events = []   # (timestamp, page, snapshot_text, source)
    report = {}
    for page in _select(fetch.load_pages(), args.only):
        pid = f"{page['vendor']}/{page['slug']}"
        ok, why = fetch.robots_allows(page["url"])
        if not ok:
            report[pid] = {"skipped": why}
            log(f"{pid}: skipped ({why})")
            continue
        caps = []
        for u in [page["url"], *page.get("aliases", [])]:
            caps += fetch.cdx_captures(u, args.since, args.until)
        by_day = {}
        for c in sorted(caps, key=lambda c: c["timestamp"]):
            by_day.setdefault(c["timestamp"][:8], c)   # one capture per day, any alias
        caps = list(by_day.values())
        picks = _weekly(caps, args.every_days)
        rows, prev_digest, prev_html = [], None, None
        for c in picks:
            stamp = "wb-" + c["timestamp"]
            html = fetch.cached(page, stamp)
            if html is None:
                if c["digest"] == prev_digest and prev_html is not None:
                    html = prev_html
                else:
                    try:
                        status, html = fetch.fetch_wayback(c["timestamp"], c["original"])
                    except Exception as e:  # noqa: BLE001
                        log(f"  {pid} {c['timestamp']}: {e!r}"[:200])
                        continue
                    if status != 200:
                        log(f"  {pid} {c['timestamp']}: HTTP {status}")
                        continue
                fetch.store_cache(page, stamp, html)
            prev_digest, prev_html = c["digest"], html
            body = html_to_markdown(html, page.get("select"))
            rows.append((c["timestamp"], body, snapshot_text(page, html)))
        # Drop captures that are bot walls, JS shells or a fraction of the usual size;
        # otherwise one bad capture shows up as "page gutted" then "page restored".
        good, dropped = [], []
        med = statistics.median([len(r[1]) for r in rows]) if rows else 0
        for ts, body, text in rows:
            bad = store.looks_broken(body) or (
                "under half the page's median size" if len(body) < 0.5 * med else None)
            (dropped if bad else good).append((ts, bad))
            if not bad:
                events.append((ts, page, text, f"wayback {ts}"))
        report[pid] = {"captures_in_window": len(caps), "sampled": len(picks),
                       "used": len(good), "dropped": [d for d in dropped]}
        log(f"{pid}: {len(caps)} daily captures, sampled {len(picks)}, used {len(good)}, "
            f"dropped {len(dropped)}")

    events.sort(key=lambda e: e[0])
    (fetch.ROOT / "data").mkdir(exist_ok=True)
    (fetch.ROOT / "data" / "backfill-report.json").write_text(
        json.dumps(report, indent=1), encoding="utf-8")
    if args.dry_run:
        log(f"dry run: {len(events)} usable captures, nothing committed")
        return 0
    commits = 0
    for ts, page, text, source in events:
        when = dt.datetime.strptime(ts, "%Y%m%d%H%M%S").replace(tzinfo=dt.timezone.utc).isoformat()
        if store.commit_snapshot(page, text, when, source):
            commits += 1
    log(f"backfill: {commits} snapshot commits from {len(events)} usable captures")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="fineprint")
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch")
    f.add_argument("--only", nargs="*")
    b = sub.add_parser("backfill")
    b.add_argument("since")
    b.add_argument("until")
    b.add_argument("--every-days", type=int, default=7)
    b.add_argument("--only", nargs="*")
    b.add_argument("--dry-run", action="store_true")
    s = sub.add_parser("summarize")
    s.add_argument("--limit", type=int, default=0)
    s.add_argument("--no-llm", action="store_true")
    sub.add_parser("build")
    args = ap.parse_args(argv)
    if args.cmd == "fetch":
        return cmd_fetch(args)
    if args.cmd == "backfill":
        return cmd_backfill(args)
    if args.cmd == "summarize":
        from .summarize import run
        return run(limit=args.limit, use_llm=not args.no_llm)
    if args.cmd == "build":
        from .site import build
        return build()
    return 1


if __name__ == "__main__":
    t0 = time.time()
    rc = main()
    log(f"done in {time.time() - t0:.0f}s")
    sys.exit(rc)
