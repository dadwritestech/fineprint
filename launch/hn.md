# Show HN

Title (80 chars max):

    Show HN: Fineprint – git log for what AI companies quietly changed

URL:

    https://github.com/dadwritestech/fineprint

Leave the text field empty. The first comment is for the maintainer to write in their own words. Notes for it:

- 46 public pricing, limits, terms, privacy and deprecation pages from 10 vendors, snapshotted into git. Each change is one commit.
- 6 months of history rebuilt from weekly Wayback captures: 397 changes, 355 non-cosmetic.
- Normalizer tests make sure noise (timestamps, cookie banners, CDN hashes) never produces a diff.
- The summaries are from a 12B local model and scored 27/30 on a hand check. Every line links its diff. Real example: a summary said Google dropped free Search grounding, but the diff shows only one model's row changed.
- Ask: which pages are missing?
