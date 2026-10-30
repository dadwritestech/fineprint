"""Static site: index, one timeline per vendor, one page per diff, RSS."""
from __future__ import annotations

import datetime as dt
import html
import json
import os
from collections import defaultdict
from email.utils import format_datetime

from .fetch import ROOT, load_pages
from .summarize import load_changes

SITE = ROOT / "site"
BASE = os.environ.get("FINEPRINT_BASE_URL", "https://dadwritestech.github.io/fineprint/")
REPO = os.environ.get("FINEPRINT_REPO_URL", "https://github.com/dadwritestech/fineprint")
FEED_ITEMS = 60

VENDOR_NAMES = {
    "anthropic": "Anthropic", "openai": "OpenAI", "google": "Google Gemini", "xai": "xAI",
    "mistral": "Mistral", "cursor": "Cursor", "github-copilot": "GitHub Copilot",
    "perplexity": "Perplexity", "deepseek": "DeepSeek", "groq": "Groq",
}

CSS = """
:root{--paper:#f6f3ec;--ink:#1d1b17;--muted:#6f685c;--rule:#d9d2c3;--red:#b3261e;--add:#e3f1e0;--del:#f7e1de;--card:#fffdf8}
@media (prefers-color-scheme:dark){:root{--paper:#16140f;--ink:#ece6d9;--muted:#9a917f;--rule:#38332a;--red:#ff7a6e;--add:#1d3320;--del:#3d1f1b;--card:#1d1a14}}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.55 "Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif}
a{color:inherit;text-decoration-color:var(--red);text-underline-offset:3px}
.wrap{max-width:880px;margin:0 auto;padding:40px 24px 80px}
header.top{display:flex;justify-content:space-between;align-items:baseline;border-bottom:3px double var(--ink);padding-bottom:14px;margin-bottom:28px;gap:16px;flex-wrap:wrap}
.brand{font-size:30px;font-weight:700;letter-spacing:-.5px;text-decoration:none}
.brand span{color:var(--red)}
.tag{font:13px/1.4 ui-monospace,"Cascadia Mono",Consolas,monospace;color:var(--muted)}
h1{font-size:40px;line-height:1.1;margin:0 0 6px;letter-spacing:-.8px}
.lede{color:var(--muted);margin:0 0 30px;max-width:640px}
.mono{font-family:ui-monospace,"Cascadia Mono",Consolas,monospace;font-size:13px}
.vendors{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:12px;margin:0 0 40px}
.vendors a{display:block;background:var(--card);border:1px solid var(--rule);padding:14px 16px;text-decoration:none}
.vendors a:hover{border-color:var(--ink)}
.vendors b{display:block;font-size:18px}
.month{font:600 12px/1 ui-monospace,Consolas,monospace;letter-spacing:.12em;text-transform:uppercase;color:var(--red);margin:34px 0 8px;padding-bottom:6px;border-bottom:1px solid var(--rule)}
ol.tl{list-style:none;margin:0;padding:0}
ol.tl li{display:grid;grid-template-columns:92px 1fr;gap:4px 18px;padding:12px 0;border-bottom:1px dotted var(--rule)}
ol.tl li.minor{opacity:.55}
.date{font:13px/1.9 ui-monospace,Consolas,monospace;color:var(--muted)}
.what{font-size:17px}
.meta{grid-column:2;font:12px/1.4 ui-monospace,Consolas,monospace;color:var(--muted);display:flex;gap:12px;flex-wrap:wrap}
.chip{border:1px solid var(--rule);padding:0 6px;border-radius:2px}
.plus{color:#2e7d32}.minus{color:var(--red)}
.note{border-left:3px solid var(--red);padding:8px 14px;background:var(--card);color:var(--muted);font-size:14px;margin:0 0 26px}
pre.diff{background:var(--card);border:1px solid var(--rule);padding:12px 0;overflow-x:auto;font:12.5px/1.5 ui-monospace,Consolas,monospace;white-space:pre-wrap;word-break:break-word}
pre.diff span{display:block;padding:0 14px}
pre.diff .a{background:var(--add)}pre.diff .d{background:var(--del)}pre.diff .h{color:var(--muted)}
footer{margin-top:50px;color:var(--muted);font-size:13px;border-top:1px solid var(--rule);padding-top:14px}
"""


def _e(s: str) -> str:
    return html.escape(s, quote=True)


def _page(title: str, body: str, depth: int = 0) -> str:
    up = "../" * depth
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_e(title)}</title><link rel="alternate" type="application/rss+xml" title="fineprint" href="{up}feed.xml">
<style>{CSS}</style></head><body><div class="wrap">
<header class="top"><a class="brand" href="{up}index.html">fine<span>print</span></a>
<span class="tag">what AI companies quietly changed &middot; <a href="{up}feed.xml">RSS</a></span></header>
{body}
<footer>Snapshots of public, logged-out pages, normalized to markdown and committed to git.
One-line summaries are written by a local LLM and can be wrong: every entry links the raw diff, which is the source of truth.
History before the first live fetch is reconstructed from Wayback Machine captures sampled about weekly, so dates are "first seen in a capture", not exact change times.</footer>
</div></body></html>"""


def _when(iso: str) -> dt.datetime:
    return dt.datetime.fromisoformat(iso).astimezone(dt.timezone.utc)


def _entry(r: dict, up: str, show_vendor: bool) -> str:
    d = _when(r["date"])
    who = f"{VENDOR_NAMES.get(r['vendor'], r['vendor'])} &middot; " if show_vendor else ""
    return (f'<li class="{"minor" if r["minor"] else ""}"><span class="date">{d:%b %d}</span>'
            f'<span class="what">{_e(r["summary"])}</span>'
            f'<span class="meta"><span class="chip">{who}{_e(r["slug"])}</span>'
            f'<span class="chip">{_e(r["kind"])}</span>'
            f'<span><span class="plus">+{r["added"]}</span> <span class="minus">&minus;{r["removed"]}</span></span>'
            f'<a href="{up}{_e(r["diff"][:-5])}.html">raw diff</a>'
            f'<a href="{_e(r["url"])}">live page</a></span></li>')


def _timeline(recs: list[dict], up: str, show_vendor: bool) -> str:
    out, month = [], None
    for r in sorted(recs, key=lambda r: r["date"], reverse=True):
        m = f"{_when(r['date']):%B %Y}"
        if m != month:
            if month is not None:
                out.append("</ol>")
            out.append(f'<div class="month">{m}</div><ol class="tl">')
            month = m
        out.append(_entry(r, up, show_vendor))
    if month is not None:
        out.append("</ol>")
    return "\n".join(out) or "<p>No changes recorded yet.</p>"


def _diff_page(r: dict) -> str:
    raw = (SITE / r["diff"]).read_text(encoding="utf-8")
    lines = []
    for ln in raw.splitlines():
        cls = "a" if ln.startswith("+") and not ln.startswith("+++") else \
              "d" if ln.startswith("-") and not ln.startswith("---") else \
              "h" if ln.startswith(("@@", "diff ", "index ", "+++", "---")) else ""
        lines.append(f'<span class="{cls}">{_e(ln) or " "}</span>')
    d = _when(r["date"])
    body = f"""<p class="mono">{d:%Y-%m-%d %H:%M} UTC &middot; {_e(r['page'])} &middot; <a href="{_e(r['url'])}">live page</a></p>
<h1 style="font-size:28px">{_e(r['summary'])}</h1>
<p class="note">Summary by {_e(r['by'])}. It may be wrong; the diff below is what actually changed.
Raw: <a href="{_e(os.path.basename(r['diff']))}">{_e(os.path.basename(r['diff']))}</a> &middot;
commit <a href="{REPO}/commit/{r['sha']}">{r['sha'][:10]}</a></p>
<pre class="diff">{''.join(lines)}</pre>
<p><a href="../{_e(r['vendor'])}.html">&larr; {VENDOR_NAMES.get(r['vendor'], r['vendor'])} timeline</a></p>"""
    return _page(f"{r['page']}: {r['summary']}", body, depth=1)


def _rss(recs: list[dict]) -> str:
    items = []
    for r in sorted(recs, key=lambda r: r["date"], reverse=True)[:FEED_ITEMS]:
        link = f"{BASE}{r['diff'][:-5]}.html"
        title = f"{VENDOR_NAMES.get(r['vendor'], r['vendor'])} {r['slug']}: {r['summary']}"
        desc = (f"{r['summary']} (+{r['added']}/-{r['removed']} lines). "
                f"Raw diff: {BASE}{r['diff']} . Page: {r['url']}")
        items.append(f"""<item><title>{_e(title)}</title><link>{_e(link)}</link>
<guid isPermaLink="false">{_e(r['id'])}</guid><pubDate>{format_datetime(_when(r['date']))}</pubDate>
<category>{_e(r['vendor'])}</category><category>{_e(r['kind'])}</category>
<description>{_e(desc)}</description></item>""")
    now = format_datetime(dt.datetime.now(dt.timezone.utc))
    return f"""<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0"><channel><title>fineprint: what AI companies quietly changed</title>
<link>{BASE}</link><description>Diffs of AI vendors' pricing, limits, policies, terms and deprecation pages. Minor wording changes are excluded.</description>
<lastBuildDate>{now}</lastBuildDate>
{chr(10).join(items)}
</channel></rss>
"""


def build() -> int:
    recs = list(load_changes().values())
    pages = load_pages()
    by_vendor: dict[str, list[dict]] = defaultdict(list)
    for r in recs:
        by_vendor[r["vendor"]].append(r)
    vendors = list(dict.fromkeys(p["vendor"] for p in pages))
    watched = defaultdict(list)
    for p in pages:
        watched[p["vendor"]].append(p)

    for r in recs:
        (SITE / "diffs" / f"{r['id']}.html").write_text(_diff_page(r), encoding="utf-8")

    cards = []
    for v in vendors:
        rs = by_vendor.get(v, [])
        major = [r for r in rs if not r["minor"]]
        last = max((r["date"] for r in rs), default=None)
        cards.append(f'<a href="{v}.html"><b>{VENDOR_NAMES.get(v, v)}</b>'
                     f'<span class="mono">{len(major)} changes &middot; {len(watched[v])} pages</span><br>'
                     f'<span class="mono">last: {_when(last):%Y-%m-%d}</span></a>' if last else
                     f'<a href="{v}.html"><b>{VENDOR_NAMES.get(v, v)}</b>'
                     f'<span class="mono">{len(watched[v])} pages &middot; no changes yet</span></a>')
        pl = "".join(f'<li><a href="{_e(p["url"])}">{_e(p["slug"])}</a> <span class="mono">({_e(p["kind"])})</span></li>'
                     for p in watched[v])
        body = (f"<h1>{VENDOR_NAMES.get(v, v)}</h1><p class='lede'>Every recorded change to "
                f"{len(watched[v])} public pages. Faded entries are wording-only changes.</p>"
                + _timeline(rs, "", False)
                + f"<div class='month'>Pages watched</div><ul>{pl}</ul>")
        (SITE / f"{v}.html").write_text(_page(f"fineprint: {VENDOR_NAMES.get(v, v)}", body),
                                        encoding="utf-8")

    major = [r for r in recs if not r["minor"]]
    span = ""
    if recs:
        lo, hi = min(r["date"] for r in recs), max(r["date"] for r in recs)
        span = f"{_when(lo):%b %d, %Y} to {_when(hi):%b %d, %Y}"
    body = (f"<h1>What AI companies quietly changed.</h1>"
            f"<p class='lede'>{len(pages)} pricing, limits, policy, terms and deprecation pages across "
            f"{len(vendors)} vendors. {len(major)} substantive changes recorded, {span}.</p>"
            f"<div class='vendors'>{''.join(cards)}</div>"
            + _timeline(major[:], "", True))
    (SITE / "index.html").write_text(_page("fineprint: what AI companies quietly changed", body),
                                     encoding="utf-8")
    (SITE / "feed.xml").write_text(_rss(major), encoding="utf-8")
    (SITE / "changes.json").write_text(json.dumps(sorted(recs, key=lambda r: r["date"]), indent=1),
                                       encoding="utf-8")
    print(f"built site: {len(recs)} changes, {len(vendors)} vendor pages", flush=True)
    return 0
