"""Snapshots live in git. One commit per page change, dated at capture time."""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from .fetch import ROOT

BOT = ("fineprint-bot", "fineprint-bot@users.noreply.github.com")
CHALLENGE = re.compile(r"just a moment\.\.\.|enable javascript and cookies to continue|"
                       r"attention required! \| cloudflare|verify you are human|"
                       r"access denied|request blocked|checking your browser", re.I)


def snapshot_path(page: dict) -> Path:
    return ROOT / "snapshots" / page["vendor"] / f"{page['slug']}.md"


def git(*args: str, env: dict | None = None, check: bool = True) -> str:
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", env={**os.environ, **(env or {})})
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout


def looks_broken(md_body: str) -> str | None:
    """Reasons a capture should not become a snapshot (bot wall, empty shell)."""
    if CHALLENGE.search(md_body[:3000]):
        return "bot challenge / block page"
    if md_body.count("�") > max(20, len(md_body) // 200):
        return "undecodable bytes (compressed or wrong charset)"
    if len(md_body.strip()) < 200:
        return "near-empty page (JS shell?)"
    return None


def commit_snapshot(page: dict, text: str, when_iso: str, source: str) -> str | None:
    """Write the snapshot and commit it if it changed. Returns the new sha or None."""
    path = snapshot_path(page)
    old = path.read_text(encoding="utf-8") if path.exists() else None
    if old == text:
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))
    rel = path.relative_to(ROOT).as_posix()
    git("add", "--", rel)
    pid = f"{page['vendor']}/{page['slug']}"
    subject = f"{pid}: first snapshot" if old is None else f"{pid}: page changed"
    body = f"source: {source}\nurl: {page['url']}\ncaptured: {when_iso}"
    env = {"GIT_AUTHOR_NAME": BOT[0], "GIT_AUTHOR_EMAIL": BOT[1],
           "GIT_COMMITTER_NAME": BOT[0], "GIT_COMMITTER_EMAIL": BOT[1],
           "GIT_AUTHOR_DATE": when_iso, "GIT_COMMITTER_DATE": when_iso}
    git("commit", "-q", "-m", subject, "-m", body, "--", rel, env=env)
    return git("rev-parse", "HEAD").strip()
