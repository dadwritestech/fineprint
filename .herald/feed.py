"""fineprint feed for herald: one post per substantive vendor change from the last 14 days."""
import datetime as dt
import json
import os

ROOT = os.path.join(os.path.dirname(__file__), "..")
SITE = "https://dadwritestech.github.io/fineprint"
NAMES = {"anthropic": "Anthropic", "google": "Google", "openai": "OpenAI", "mistral": "Mistral",
         "xai": "xAI", "github-copilot": "GitHub Copilot", "deepseek": "DeepSeek",
         "cursor": "Cursor", "perplexity": "Perplexity", "groq": "Groq"}
# Pricing, limits and terms changes matter most to people paying; changelog noise matters least.
WEIGHT = {"pricing": 3, "limits": 3, "terms": 3, "privacy": 3, "policy": 2, "deprecations": 2,
          "changelog": 0}


def main(now=None, days=14):
    now = now or dt.datetime.now(dt.timezone.utc)
    cutoff = now - dt.timedelta(days=days)
    rows = [json.loads(l) for l in open(os.path.join(ROOT, "data", "changes.jsonl"), encoding="utf-8")]
    for c in reversed(rows):  # newest first, so fresh news wins ties
        if c.get("minor") or not c.get("summary"):
            continue
        when = dt.datetime.fromisoformat(c["date"].replace("Z", "+00:00"))
        if when < cutoff:
            continue
        vendor = NAMES.get(c["vendor"], c["vendor"])
        print(json.dumps({
            "id": f"fineprint/{c['id']}",
            "text": (f"{vendor} changed its {c['kind']} page ({when:%b %d}):\n\n{c['summary']}\n\n"
                     f"+{c['added']}/-{c['removed']} lines. Auto-summary; the diff is the record."),
            "link": f"{SITE}/{c['vendor']}.html",
            "priority": WEIGHT.get(c["kind"], 1),
        }, ensure_ascii=False))


if __name__ == "__main__":
    main()
