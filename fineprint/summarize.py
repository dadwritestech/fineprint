"""One plain-English line per snapshot diff.

Every record keeps the raw diff next to the summary, so nobody has to trust
the model. Without an LLM (or if it fails), a deterministic line is used.

LLM endpoint: FINEPRINT_LLM_URL (default http://localhost:8080/v1/chat/completions),
key: FINEPRINT_LLM_KEY or LLAMA_API_KEY, model: FINEPRINT_LLM_MODEL (default gemma-4-12b).
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

import requests

from .fetch import ROOT, load_pages
from .store import git

CHANGES = ROOT / "data" / "changes.jsonl"
DIFFS = ROOT / "site" / "diffs"
MAX_DIFF_CHARS = 7000
PROMPT_VERSION = 2

SYSTEM = """You write the one-line changelog entry for a diff of an AI company's public web page.
Rules:
- One sentence, at most 25 words, plain English, no preamble, no quotes, no markdown.
- Lead with the most consequential change for users or developers: prices, limits, quotas, model names, dates, rights, obligations, data use.
- Use the concrete names and numbers that appear in the diff. Never invent or guess numbers.
- Describe only what the diff shows. Lines starting with - were removed, + were added.
- If the change is only wording, typo, formatting or reordering with no change in meaning, start with "Minor:".
"""


def _key() -> str | None:
    return os.environ.get("FINEPRINT_LLM_KEY") or os.environ.get("LLAMA_API_KEY")


def _changed_lines(diff: str) -> tuple[list[str], list[str]]:
    add, rem = [], []
    for ln in diff.splitlines():
        if ln.startswith("+++") or ln.startswith("---"):
            continue
        if ln.startswith("+") and ln[1:].strip():
            add.append(ln[1:].strip())
        elif ln.startswith("-") and ln[1:].strip():
            rem.append(ln[1:].strip())
    return add, rem


def fallback_summary(diff: str) -> str:
    add, rem = _changed_lines(diff)
    heads = [ln.lstrip("# ") for ln in add + rem if ln.startswith("#")]
    where = f" (around \"{heads[0][:60]}\")" if heads else ""
    return f"{len(add)} line(s) added, {len(rem)} removed{where}."


def llm_summary(page: dict, diff: str) -> str:
    body = diff if len(diff) <= MAX_DIFF_CHARS else (
        diff[:MAX_DIFF_CHARS] + f"\n[... diff truncated, {len(diff) - MAX_DIFF_CHARS} more chars]")
    user = (f"Vendor: {page['vendor']}\nPage: {page['slug']} ({page['kind']} page)\n"
            f"URL: {page['url']}\n\nUnified diff:\n{body}\n\nWrite the one-line entry.")
    payload = {
        "model": os.environ.get("FINEPRINT_LLM_MODEL", "gemma-4-12b"),
        "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}],
        "temperature": 0.1,
        "max_tokens": 90,
        # gemma-4 reasons by default; this is the only switch that turns it off
        "chat_template_kwargs": {"enable_thinking": False},
    }
    url = os.environ.get("FINEPRINT_LLM_URL", "http://localhost:8080/v1/chat/completions")
    headers = {"Authorization": f"Bearer {_key()}"} if _key() else {}
    r = requests.post(url, json=payload, headers=headers, timeout=180)
    r.raise_for_status()
    text = r.json()["choices"][0]["message"]["content"]
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
    text = text.splitlines()[0].strip().strip('"').strip("*").strip() if text else ""
    if not text:
        raise ValueError("empty completion")
    return text


def snapshot_commits() -> list[dict]:
    """Every (commit, snapshot file) pair, oldest first by capture date."""
    out = git("log", "--reverse", "--format=@@%H\t%aI", "--name-status", "--", "snapshots/")
    rows, sha, date = [], None, None
    for line in out.splitlines():
        if line.startswith("@@"):
            sha, date = line[2:].split("\t")
        elif line.strip():
            status, path = line.split("\t", 1)
            rows.append({"sha": sha, "date": date, "status": status[0], "path": path})
    rows.sort(key=lambda r: r["date"])
    return rows


def load_changes() -> dict[str, dict]:
    if not CHANGES.exists():
        return {}
    recs = [json.loads(l) for l in CHANGES.read_text(encoding="utf-8").splitlines() if l.strip()]
    return {r["id"]: r for r in recs}


def save_changes(recs: dict[str, dict]) -> None:
    CHANGES.parent.mkdir(exist_ok=True)
    ordered = sorted(recs.values(), key=lambda r: (r["date"], r["page"]))
    CHANGES.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in ordered),
                       encoding="utf-8")


def run(limit: int = 0, use_llm: bool = True) -> int:
    pages = {f"snapshots/{p['vendor']}/{p['slug']}.md": p for p in load_pages()}
    recs = load_changes()
    DIFFS.mkdir(parents=True, exist_ok=True)
    done = 0
    for row in snapshot_commits():
        page = pages.get(row["path"])
        if page is None or row["status"] != "M":
            continue   # first snapshots are not changes
        rid = f"{row['sha'][:10]}-{page['vendor']}-{page['slug']}"
        rec = recs.get(rid)
        if rec and (rec["by"] != "fallback" or not use_llm) and rec.get("v") == PROMPT_VERSION:
            continue
        diff = git("diff", "--unified=2", f"{row['sha']}^", row["sha"], "--", row["path"])
        (DIFFS / f"{rid}.diff").write_text(diff, encoding="utf-8", newline="\n")
        add, rem = _changed_lines(diff)
        summary, by = None, "fallback"
        if use_llm:
            try:
                t0 = time.time()
                summary, by = llm_summary(page, diff), os.environ.get("FINEPRINT_LLM_MODEL", "gemma-4-12b")
                print(f"{row['date'][:10]} {page['vendor']}/{page['slug']} ({time.time() - t0:.1f}s): {summary}",
                      flush=True)
            except Exception as e:  # noqa: BLE001
                print(f"llm failed for {rid}: {e!r}"[:200], flush=True)
        if summary is None:
            summary = fallback_summary(diff)
        recs[rid] = {
            "id": rid, "v": PROMPT_VERSION, "date": row["date"], "sha": row["sha"],
            "page": f"{page['vendor']}/{page['slug']}", "vendor": page["vendor"],
            "slug": page["slug"], "kind": page["kind"], "url": page["url"],
            "summary": summary, "minor": summary.lower().startswith("minor:"), "by": by,
            "added": len(add), "removed": len(rem), "diff": f"diffs/{rid}.diff",
        }
        save_changes(recs)   # save every step: the run is resumable
        done += 1
        if limit and done >= limit:
            break
    print(f"summarized {done} change(s); {len(recs)} total", flush=True)
    return 0
