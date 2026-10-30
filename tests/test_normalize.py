"""Noise must produce zero diff; real edits must produce a diff."""
import pytest

from fineprint.normalize import html_to_markdown, snapshot_text

BASE = """<!doctype html><html><head><title>Pricing</title>
<meta name="build" content="{build}"><link rel="stylesheet" href="/_next/static/{build}.css">
<script nonce="{nonce}">window.__NEXT_DATA__={{"buildId":"{build}","ts":{ts}}}</script>
<style>.x{{color:red}}</style></head>
<body>
<header><nav><a href="/">Home</a><a href="/pricing?ref={nonce}">Pricing</a></nav></header>
{banner}
<main class="{cls}">
  <h1>Plans &amp; pricing</h1>
  <p>Last updated: May 1, 2026</p>
  <p>The <strong>Pro</strong> plan costs <a href="/buy?utm_source={nonce}">$20{sp}per month</a>.</p>
  <ul><li>Up to 5x more usage than Free</li><li>Access to “Projects”</li></ul>
  <table><tr><th>Model</th><th>Input</th><th>Output</th></tr>
         <tr><td>Big</td><td>$3 / MTok</td><td>$15 / MTok</td></tr></table>
  <p>Contact <a href="/cdn-cgi/l/email-protection" class="__cf_email__" data-cfemail="{cf}">[email&#160;protected]</a></p>
  <p class="text-sm text-gray-500">Updated {ago} ago</p>
  <div class="sr-only">Opens in a new tab</div>
  <div class="feedback-widget">Was this page helpful? <button>Yes</button><button>No</button></div>
  <img src="/hero.{build}.png" alt="hero {build}">
  <form><input type="hidden" name="csrf" value="{nonce}"></form>
</main>
<footer>© {year} Example Inc. All rights reserved.</footer>
</body></html>"""


def cf_encode(email: str, key: int) -> str:
    return f"{key:02x}" + "".join(f"{ord(c) ^ key:02x}" for c in email)


DEFAULTS = dict(build="a1b2c3", nonce="n0nce1", ts=1714000000, banner="", cls="page_main__x1y2",
                sp=" ", cf=cf_encode("sales@example.com", 0x42), ago="3 hours", year="2025")


def render(**over):
    return BASE.format(**{**DEFAULTS, **over})


def md(**over):
    return html_to_markdown(render(**over))


NOISE = {
    "build hash + script payload": dict(build="zz99", ts=1799999999),
    "csp nonce / csrf / tracking params": dict(nonce="other-nonce-777"),
    "cookie banner injected": dict(banner='<div id="onetrust-consent-sdk"><p>We use cookies to improve '
                                          'your experience.</p><button>Accept all</button></div>'),
    "role=dialog consent": dict(banner='<div role="dialog"><p>Your privacy choices</p></div>'),
    "css-module class names": dict(cls="page_main__Q9w8e"),
    "nbsp vs space": dict(sp="&nbsp;"),
    "narrow nbsp": dict(sp=" "),
    "cloudflare email key rotates": dict(cf=cf_encode("sales@example.com", 0x7f)),
    "relative timestamp": dict(ago="5 minutes"),
    "copyright year": dict(year="2026"),
}


@pytest.mark.parametrize("name", list(NOISE))
def test_noise_produces_no_diff(name):
    assert md(**NOISE[name]) == md(), name


def test_all_noise_at_once():
    combined = {}
    for v in NOISE.values():
        combined.update(v)
    assert md(**combined) == md()


def test_whitespace_and_attribute_order_noise():
    a = render()
    b = (a.replace("<p>The", "<p   data-x='1'>\n\n   The")
          .replace("</li><li>", "</li>\n   \t<li>")
          .replace("<h1>", "<h1 id=\"top\"  class=\"title\">"))
    assert html_to_markdown(a) == html_to_markdown(b)


def test_wayback_toolbar_is_stripped():
    a = render()
    b = a.replace("<body>", "<body><!-- BEGIN WAYBACK TOOLBAR INSERT --><div id='wm-ipp'>"
                            "<p>The Wayback Machine - captured 12 times</p></div>"
                            "<!-- END WAYBACK TOOLBAR INSERT -->")
    assert html_to_markdown(a) == html_to_markdown(b)


def test_html_comments_are_ignored():
    a = render()
    b = a.replace("<h1>", "<!-- rendered at 2026-10-30T11:22:33Z by node-7 --><h1>")
    assert html_to_markdown(a) == html_to_markdown(b)


def test_smart_quotes_fold_to_ascii():
    a = render()
    b = a.replace("“Projects”", '"Projects"')
    assert html_to_markdown(a) == html_to_markdown(b)


# --- real changes must still show up -----------------------------------------

@pytest.mark.parametrize("old,new", [
    ("$20", "$25"),
    ("Up to 5x more usage", "Up to 3x more usage"),
    ("$15 / MTok", "$12 / MTok"),
    ("Last updated: May 1, 2026", "Last updated: June 3, 2026"),
    ("<li>Access to “Projects”</li>", ""),
])
def test_real_change_produces_diff(old, new):
    a = render()
    b = a.replace(old, new)
    assert a != b
    assert html_to_markdown(a) != html_to_markdown(b)


def test_emails_are_decoded_so_a_real_contact_change_shows():
    assert "sales@example.com" in md()
    assert md(cf=cf_encode("legal@example.com", 0x11)) != md()


def test_expected_shape():
    out = md()
    assert "# Plans & pricing" in out
    assert "- Up to 5x more usage than Free" in out
    assert "| Big | $3 / MTok | $15 / MTok |" in out
    assert 'Access to "Projects"' in out
    for junk in ("Home", "cookies", "Opens in a new tab", "helpful", "Rights reserved",
                 "a1b2c3", "n0nce1", "hours ago", "©"):
        assert junk.lower() not in out.lower(), junk


def test_output_is_idempotent_and_newline_terminated():
    out = md()
    assert out.endswith("\n") and not out.endswith("\n\n")
    assert "\n\n\n" not in out


def test_thin_main_falls_back_to_body():
    html = ("<body><main><p>Hi</p></main><section><h2>Terms</h2><p>" + "word " * 200 +
            "</p></section></body>")
    assert "## Terms" in html_to_markdown(html)


def test_snapshot_header_has_no_time():
    page = {"vendor": "v", "slug": "s", "url": "https://x"}
    assert snapshot_text(page, render()) == snapshot_text(page, render(**NOISE["relative timestamp"]))
    assert snapshot_text(page, render()).startswith("<!-- fineprint snapshot: v/s | source: https://x -->")


def test_tailwind_variant_classes_are_not_noise():
    html = ('<main><div class="toc-visible:md:grid-cols-10 grid [--gap:8px]">'
            '<p>' + 'Policy text. ' * 30 + '</p></div><div class="toc"><p>Contents</p></div></main>')
    out = html_to_markdown(html)
    assert "Policy text." in out
    assert "Contents" not in out


def test_broken_captures_are_detected():
    from fineprint.store import looks_broken
    assert looks_broken("Just a moment... Enable JavaScript and cookies to continue")
    assert looks_broken("tiny")
    assert looks_broken("ok text " * 50 + "�" * 300)
    assert looks_broken(md()) is None
