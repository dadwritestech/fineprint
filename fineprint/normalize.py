"""HTML -> stable markdown.

The goal is not pretty markdown. The goal is that two fetches of an unchanged
page produce byte-identical output, so every git diff is a real change.

What we throw away, and why:
- scripts, styles, svg, forms, nav/header/footer/aside: never policy text, and
  full of build hashes, nonces and CSRF tokens.
- link targets and images: URLs churn (locale, tracking params, CDN hashes,
  Wayback rewriting); the link *text* is kept.
- emphasis markers: bold/italic toggles are design changes, not policy changes.
- relative timestamps ("3 hours ago"), copyright lines, cookie banners,
  "was this page helpful" widgets, screen-reader-only text.
What we keep on purpose: absolute dates such as "Last updated: May 1, 2026".
A vendor bumping that date is itself a signal.
"""
from __future__ import annotations

import re
import unicodedata

from bs4 import BeautifulSoup, Comment, NavigableString, Tag

DROP_TAGS = {
    "script", "style", "noscript", "template", "svg", "canvas", "iframe",
    "form", "button", "input", "select", "textarea", "nav", "header",
    "footer", "aside", "dialog", "link", "meta", "object", "embed", "video",
    "audio", "picture", "img", "source", "head", "title",
}
DROP_ROLES = {"navigation", "banner", "contentinfo", "dialog", "search",
              "alertdialog", "complementary", "menu", "menubar", "toolbar"}
# Matched against each class/id token, split on - and _ .
NOISE_WORDS = {
    "cookie", "cookies", "consent", "onetrust", "gdpr", "newsletter",
    "breadcrumb", "breadcrumbs", "toc", "sidebar", "feedback", "sronly",
    "visuallyhidden", "skip", "announcement", "toast", "intercom",
    "pagination", "pager", "copybutton", "anchor",
}
NOISE_PHRASES = ("sr-only", "visually-hidden", "table-of-contents", "skip-link",
                 "skip-to", "was-this-helpful", "edit-this-page", "on-this-page")

BLOCK = {"p", "div", "section", "article", "main", "body", "html", "ul", "ol",
         "li", "table", "h1", "h2", "h3", "h4", "h5", "h6", "pre", "blockquote",
         "dl", "dt", "dd", "details", "summary", "figure", "figcaption", "hr",
         "tr", "thead", "tbody", "tfoot"}

WAYBACK_TOOLBAR = re.compile(
    r"<!--\s*BEGIN WAYBACK TOOLBAR INSERT\s*-->.*?<!--\s*END WAYBACK TOOLBAR INSERT\s*-->",
    re.S | re.I)

CHAR_MAP = str.maketrans({
    "\u00a0": ' ',
    "\u202f": ' ',
    "\u2007": ' ',
    "\u2009": ' ',
    "\u200a": ' ',
    "\u2002": ' ',
    "\u2003": ' ',
    "\u3000": ' ',
    "\u200b": '',
    "\u200c": '',
    "\u200d": '',
    "\u2060": '',
    "\ufeff": '',
    "\u00ad": '',
    "\u2018": "'",
    "\u2019": "'",
    "\u201a": "'",
    "\u201b": "'",
    "\u2032": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u201e": '"',
    "\u2033": '"',
    "\u2026": '...',
    "\u2212": '-',
})

LINE_NOISE = [
    re.compile(r"^\W*(©|\(c\)|copyright)\s*(\d{4})?.*$", re.I),
    re.compile(r"^.*\b\d+\s+(second|minute|hour|day|week|month|year)s?\s+ago\b.*$", re.I),
    re.compile(r"^(just now|yesterday|today)$", re.I),
    re.compile(r"^was this (page|article) helpful\??.*$", re.I),
    re.compile(r"^(yes|no|copy|copied!?|copy page|copy link|ask ai|on this page|"
               r"skip to (main )?content|loading\.*|menu|close|open menu|"
               r"toggle (navigation|menu|theme|sidebar)|back to top)$", re.I),
    re.compile(r"^(we use cookies|this (site|website) uses cookies).*$", re.I),
    re.compile(r"^(read|reading) time:?.*$", re.I),
    re.compile(r"^\d+\s+min(ute)?s?\s+read$", re.I),
]


def _decode_cfemail(hexstr: str) -> str:
    try:
        key = int(hexstr[:2], 16)
        return "".join(chr(int(hexstr[i:i + 2], 16) ^ key) for i in range(2, len(hexstr), 2))
    except ValueError:
        return ""


def _is_noise(el: Tag) -> bool:
    if el.name in DROP_TAGS:
        return True
    attrs = el.attrs or {}
    if attrs.get("role") in DROP_ROLES:
        return True
    if attrs.get("aria-hidden") == "true" or "hidden" in attrs:
        return True
    style = str(attrs.get("style", "")).replace(" ", "").lower()
    if "display:none" in style or "visibility:hidden" in style:
        return True
    names = list(attrs.get("class") or []) + [str(attrs.get("id", ""))]
    for name in names:
        low = name.lower()
        # Tailwind variants ("toc-visible:md:grid") style the page; they do not name it.
        if ":" in low or "[" in low:
            continue
        if any(p in low for p in NOISE_PHRASES):
            return True
        tokens = re.split(r"[-_]+", low)
        if any(t in NOISE_WORDS for t in tokens):
            return True
    return False


def clean_text(s: str) -> str:
    s = unicodedata.normalize("NFC", s).translate(CHAR_MAP)
    return re.sub(r"\s+", " ", s)


def _pick_root(soup: BeautifulSoup, select: str | None) -> Tag:
    if select:
        hit = soup.select_one(select)
        if hit is not None:
            return hit
    body = soup.body or soup
    body_len = len(body.get_text(" ", strip=True))
    for sel in ("main", "article", "[role=main]"):
        hit = soup.select_one(sel)
        # Some sites wrap only a hero in <main>; fall back if it is a sliver.
        if hit is not None and len(hit.get_text(" ", strip=True)) >= 0.3 * body_len:
            return hit
    return body


class _MD:
    def __init__(self) -> None:
        self.out: list[str] = []

    def block(self, text: str) -> None:
        text = text.strip()
        if text:
            self.out.append(text)

    def inline(self, el) -> str:
        if isinstance(el, NavigableString):
            if isinstance(el, Comment):
                return ""
            return clean_text(str(el))
        if not isinstance(el, Tag) or _is_noise(el):
            return ""
        if el.name == "br":
            return " "
        if el.name == "a" and el.get("data-cfemail"):
            return _decode_cfemail(el["data-cfemail"])
        if el.has_attr("data-cfemail"):
            return _decode_cfemail(el["data-cfemail"])
        if el.name == "code":
            t = clean_text(el.get_text()).strip()
            return f"`{t}`" if t else ""
        return "".join(self.inline(c) for c in el.children)

    def walk(self, el: Tag, depth: int = 0) -> None:
        buf: list[str] = []

        def flush() -> None:
            if buf:
                self.block("".join(buf))
                buf.clear()

        for child in el.children:
            if isinstance(child, NavigableString):
                buf.append(self.inline(child))
                continue
            if not isinstance(child, Tag) or _is_noise(child):
                continue
            name = child.name
            if name not in BLOCK and not self._has_block(child):
                buf.append(self.inline(child))
                continue
            flush()
            if name in {"h1", "h2", "h3", "h4", "h5", "h6"}:
                t = self.inline(child).strip()
                if t:
                    self.block("#" * int(name[1]) + " " + t)
            elif name in {"ul", "ol"}:
                self._list(child, ordered=(name == "ol"), depth=depth)
            elif name == "table":
                self._table(child)
            elif name == "pre":
                code = child.get_text().translate(CHAR_MAP).rstrip()
                code = "\n".join(line.rstrip() for line in code.splitlines())
                if code.strip():
                    self.block("```\n" + code.strip("\n") + "\n```")
            elif name == "blockquote":
                sub = _MD()
                sub.walk(child, depth)
                for b in sub.out:
                    self.block("\n".join("> " + ln for ln in b.splitlines()))
            elif name == "hr":
                continue
            else:
                self.walk(child, depth)
        flush()

    @staticmethod
    def _has_block(el: Tag) -> bool:
        return el.find(lambda t: isinstance(t, Tag) and t.name in BLOCK) is not None

    def _list(self, el: Tag, ordered: bool, depth: int) -> None:
        start = len(self.out)
        self._list_items(el, ordered, depth)
        # one block per list, so items are not separated by blank lines
        items = self.out[start:]
        del self.out[start:]
        if items:
            self.out.append("\n".join(items))

    def _list_items(self, el: Tag, ordered: bool, depth: int) -> None:
        n = 0
        for li in el.find_all("li", recursive=False):
            if _is_noise(li):
                continue
            n += 1
            sub = _MD()
            sub.walk(li, depth + 1)
            if not sub.out:
                continue
            marker = f"{n}." if ordered else "-"
            pad = "  " * depth
            first, *rest = sub.out
            lines = [f"{pad}{marker} {first}"]
            for r in rest:
                # nested lists already carry their own indentation
                lines.append(r if r.lstrip().startswith(("-", "1.")) and r.startswith("  ")
                             else f"{pad}  {r}")
            self.out.append("\n".join(lines))

    def _table(self, el: Tag) -> None:
        rows = []
        for tr in el.find_all("tr"):
            if tr.find_parent("table") is not el:
                continue
            cells = [self.inline(td).strip().replace("|", "\\|")
                     for td in tr.find_all(["th", "td"], recursive=False)]
            if any(cells):
                rows.append(cells)
        if not rows:
            return
        width = max(len(r) for r in rows)
        rows = [r + [""] * (width - len(r)) for r in rows]
        lines = ["| " + " | ".join(rows[0]) + " |",
                 "|" + "---|" * width]
        lines += ["| " + " | ".join(r) + " |" for r in rows[1:]]
        self.out.append("\n".join(lines))


def _post(md_blocks: list[str]) -> str:
    lines: list[str] = []
    for block in md_blocks:
        for line in block.splitlines():
            line = line.rstrip()
            core = line.lstrip("#>-|* ").strip()
            if any(p.match(core) for p in LINE_NOISE):
                continue
            lines.append(line)
        lines.append("")
    text = "\n".join(lines)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text + "\n" if text else ""


def html_to_markdown(html: str, select: str | None = None) -> str:
    html = WAYBACK_TOOLBAR.sub("", html)
    soup = BeautifulSoup(html, "html.parser")
    for c in soup.find_all(string=lambda s: isinstance(s, Comment)):
        c.extract()
    root = _pick_root(soup, select)
    md = _MD()
    md.walk(root)
    return _post(md.out)


def snapshot_text(page: dict, html: str) -> str:
    """The exact bytes we commit. The header is static: no fetch time in the file."""
    body = html_to_markdown(html, page.get("select"))
    header = f"<!-- fineprint snapshot: {page['vendor']}/{page['slug']} | source: {page['url']} -->\n\n"
    return header + body
