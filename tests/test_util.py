import src.util as util


def test_aggressively_sanitize_removes_unicode_noise():
    raw = "ÂÃJosé\u00a0García\u200b"
    assert util.aggressively_sanitize(raw) == "Jose Garcia"
