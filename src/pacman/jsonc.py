"""JSON with comments.

The subject requires the configuration file to accept comments on top
of standard JSON.  Lines starting with ``#`` are mandatory; C and C++
comments plus trailing commas are supported as well, since the subject
explicitly allows extra comment styles.

Comments are replaced by nothing but the newlines they contained, so a
syntax error reported by :mod:`json` still points at the right line of
the original file.
"""

import json
from pathlib import Path
from typing import Any


class JsoncError(Exception):
    """Raised when a document cannot be read or parsed."""


def strip_comments(text: str) -> str:
    """Remove ``#``, ``//`` and ``/* */`` comments outside of strings."""
    out: list[str] = []
    index = 0
    length = len(text)
    while index < length:
        char = text[index]
        if char == '"':
            index = _copy_string(text, index, out)
            continue
        if char == "#" or text.startswith("//", index):
            while index < length and text[index] != "\n":
                index += 1
            continue
        if text.startswith("/*", index):
            index += 2
            while index < length and not text.startswith("*/", index):
                if text[index] == "\n":
                    out.append("\n")
                index += 1
            index = min(length, index + 2)
            continue
        out.append(char)
        index += 1
    return "".join(out)


def strip_trailing_commas(text: str) -> str:
    """Drop commas that directly precede a closing bracket or brace."""
    out: list[str] = []
    index = 0
    length = len(text)
    while index < length:
        char = text[index]
        if char == '"':
            index = _copy_string(text, index, out)
            continue
        if char == ",":
            look = index + 1
            while look < length and text[look] in " \t\r\n":
                look += 1
            if look < length and text[look] in "}]":
                index += 1
                continue
        out.append(char)
        index += 1
    return "".join(out)


def loads(text: str) -> Any:
    """Parse a JSON-with-comments document."""
    cleaned = strip_trailing_commas(strip_comments(text))
    if not cleaned.strip():
        raise JsoncError("the file is empty once comments are removed")
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as error:
        raise JsoncError(
            "invalid JSON at line %d column %d: %s"
            % (error.lineno, error.colno, error.msg)) from error


def load_file(path: Path) -> Any:
    """Read and parse *path*, raising :class:`JsoncError` on any problem."""
    try:
        with open(path, "r", encoding="utf-8") as stream:
            text = stream.read()
    except FileNotFoundError as error:
        raise JsoncError("file not found: %s" % path) from error
    except IsADirectoryError as error:
        raise JsoncError("'%s' is a directory, not a file" % path) from error
    except PermissionError as error:
        raise JsoncError("permission denied: %s" % path) from error
    except UnicodeDecodeError as error:
        raise JsoncError("'%s' is not valid UTF-8 text" % path) from error
    except OSError as error:
        raise JsoncError("cannot read '%s': %s" % (path, error)) from error
    return loads(text)


def _copy_string(text: str, index: int, out: list[str]) -> int:
    """Copy the JSON string starting at *index* verbatim into *out*."""
    length = len(text)
    out.append(text[index])
    index += 1
    while index < length:
        char = text[index]
        out.append(char)
        if char == "\\" and index + 1 < length:
            out.append(text[index + 1])
            index += 2
            continue
        index += 1
        if char == '"':
            break
    return index
