import re

_TS = re.compile(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?Z?")
_UUID = re.compile(r"\b[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\b")
_IP = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
_BIGNUM = re.compile(r"\b\d{4,}\b")  # offsets, ports, ids. Short numbers (503, 2) stay.


def normalize_log(line: str) -> str:
    """Strip the parts of a log line that change on every occurrence."""
    line = _TS.sub("", line)
    line = _UUID.sub("<uuid>", line)
    line = _IP.sub("<ip>", line)
    line = _BIGNUM.sub("<n>", line)
    return re.sub(r"\s+", " ", line).strip()
