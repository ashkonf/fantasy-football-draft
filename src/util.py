"""Defines utility functions."""


def aggressively_sanitize(string: str) -> str:
    return string.replace("Â", "").replace("Ã", "")
