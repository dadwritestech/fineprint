# Good first issues (open after launch)

1. **Add a vendor: Cohere** (pricing, terms, privacy, deprecations). One `pages.toml` entry per page, plus a noise check.
2. **Pricing tables lose row labels in diffs.** A line diff of a pricing card can show "$0.25" without its row, so the summarizer misreads it (e.g. a cache-read price read as an input price). Add the nearest table header or row label to each diff hunk.
3. **Per-model scope in summaries.** When only one table row in a long page changes, the summary should name the section heading (e.g. "Gemini Robotics-ER") and not generalize to the whole page.
4. **JSON Feed** next to `site/feed.xml`.
5. **Thin OpenAI/xAI history.** archive.org refused many captures of openai.com and x.ai. Run `backfill --retry-failed` and record what comes back.
