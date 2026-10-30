from fineprint.summarize import condense, fallback_summary

DIFF = """--- a/x.md
+++ b/x.md
@@ -1,4 +1,4 @@
 intro
-## Do Not Violate Laws
+### Do Not Violate Laws
-- item one
+  - item one
@@ -10,2 +10,2 @@
 context
-The Pro plan costs $20 per month.
+The Pro plan costs $25 per month.
"""


def test_condense_drops_markup_only_pairs_and_keeps_real_edits():
    out, pairs = condense(DIFF)
    assert pairs == 2
    assert "Do Not Violate" not in out
    assert "-The Pro plan costs $20 per month." in out
    assert "+The Pro plan costs $25 per month." in out


def test_condense_of_pure_reformat_is_empty():
    only_markup = "\n".join(DIFF.splitlines()[:8])
    assert condense(only_markup)[0].strip() == ""


def test_fallback_summary_counts_lines():
    assert fallback_summary(DIFF).startswith("3 line(s) added, 3 removed")
