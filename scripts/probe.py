"""One-off: check every page's robots status, live fetchability, normalized size
and how many Wayback captures exist in the backfill window."""
import json
import sys
import time

from fineprint.fetch import cdx_captures, fetch_live, load_pages, robots_allows, store_cache
from fineprint.normalize import html_to_markdown

since, until = sys.argv[1], sys.argv[2]
out = []
for p in load_pages():
    row = {"id": f"{p['vendor']}/{p['slug']}", "url": p["url"]}
    ok, why = robots_allows(p["url"])
    row["robots"] = why
    if ok:
        try:
            status, html = fetch_live(p["url"])
            row["live_status"] = status
            if status == 200:
                store_cache(p, "live-" + time.strftime("%Y%m%d%H%M%S", time.gmtime()), html)
                row["live_md_chars"] = len(html_to_markdown(html, p.get("select")))
        except Exception as e:  # noqa: BLE001
            row["live_status"] = repr(e)[:120]
        try:
            caps = cdx_captures(p["url"], since, until)
            row["wayback_days"] = len(caps)
            row["wayback_digests"] = len({c["digest"] for c in caps})
        except Exception as e:  # noqa: BLE001
            row["wayback_days"] = repr(e)[:120]
    print(json.dumps(row), flush=True)
    out.append(row)
json.dump(out, open("data/probe.json", "w"), indent=1)
