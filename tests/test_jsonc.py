"""Tests for the JSON-with-comments reader."""

import pytest

from pacman.jsonc import JsoncError, loads, strip_comments


def test_hash_comments_are_ignored() -> None:
    """Lines starting with '#' disappear."""
    assert loads('# hello\n{"a": 1}\n# bye') == {"a": 1}


def test_c_and_cpp_comments_are_ignored() -> None:
    """The optional comment styles are supported too."""
    text = '{ // one\n"a": 1, /* two\nthree */ "b": 2 }'
    assert loads(text) == {"a": 1, "b": 2}


def test_comments_inside_strings_are_kept() -> None:
    """A '#' inside a JSON string is data, not a comment."""
    assert loads('{"a": "keep # this // and /* that */"}') == {
        "a": "keep # this // and /* that */"}


def test_trailing_commas_are_tolerated() -> None:
    """A dangling comma does not break the document."""
    assert loads('{"a": [1, 2, 3,],}') == {"a": [1, 2, 3]}


def test_line_numbers_survive_comment_removal() -> None:
    """Errors still point at the right line of the original file."""
    with pytest.raises(JsoncError) as error:
        loads("# comment\n# comment\n{\n  broken\n}")
    assert "line 4" in str(error.value)


def test_empty_document_is_rejected() -> None:
    """A file made only of comments is an error, not a crash."""
    with pytest.raises(JsoncError):
        loads("# nothing at all\n")


def test_escaped_quotes_do_not_end_the_string() -> None:
    """Backslash escapes are copied verbatim."""
    assert strip_comments(r'{"a": "x\"# y"}') == r'{"a": "x\"# y"}'
