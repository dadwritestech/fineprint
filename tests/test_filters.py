from fineprint.__main__ import filter_captures

BIG = "policy text " * 100


def rows(*texts):
    return [(f"2026{i:02d}01000000", t, t) for i, t in enumerate(texts, 1)]


def test_blip_between_equal_neighbours_is_dropped():
    kept, dropped = filter_captures(rows(BIG + "A", BIG + "B", BIG + "A", BIG + "A"))
    assert [t[-1] for _, t in kept] == ["A", "A", "A"]
    assert dropped[0][1].startswith("blip")


def test_real_change_that_persists_is_kept():
    kept, dropped = filter_captures(rows(BIG + "A", BIG + "B", BIG + "B"))
    assert [t[-1] for _, t in kept] == ["A", "B", "B"]
    assert not dropped


def test_change_at_the_last_capture_is_kept():
    kept, _ = filter_captures(rows(BIG + "A", BIG + "A", BIG + "B"))
    assert kept[-1][1].endswith("B")


def test_transient_size_dip_dropped_but_persistent_shrink_kept():
    small = "short page " * 30
    kept, dropped = filter_captures(rows(BIG, small, BIG))
    assert len(kept) == 2 and "transient dip" in dropped[0][1]
    kept, dropped = filter_captures(rows(BIG, small, small))
    assert len(kept) == 3 and not dropped


def test_bot_wall_dropped():
    wall = "Just a moment... Enable JavaScript and cookies to continue " * 5
    kept, dropped = filter_captures(rows(BIG, wall, BIG + "x"))
    assert len(kept) == 2 and "challenge" in dropped[0][1]
