"""Defines utility functions."""

import unicodedata


def aggressively_sanitize(string: str) -> str:
    """Remove stray Unicode characters and normalize to ASCII.

    Many external data sources include mis-encoded bytes that show up as
    unexpected characters (for example ``Â`` or ``Ã``), as well as
    diacritics and non-breaking spaces.  This helper strips those common
    artifacts and falls back to a Unicode normalization/ASCII encoding
    pass so that downstream parsers work with clean text.
    """

    string = string.replace("Â", "").replace("Ã", "")
    normalized = unicodedata.normalize("NFKD", string).replace("\u00a0", " ")
    return normalized.encode("ascii", "ignore").decode()
