import pytest

from vernac.util import (
    strip_markdown_fence,
    normalize_progress,
    call_with_supported_args,
)

@pytest.mark.parametrize("markdown, expected", [
    (
        "```\nThis is code block\n```\n",
        "This is code block\n"
    ),
    (
        "```\nThis is code block with a language specified\n```",
        "This is code block with a language specified\n"
    ),
    (
        "```\nThis is a code block\nWith multiple lines\n```",
        "This is a code block\nWith multiple lines\n"
    ),
    (
        "This is regular text without code block",
        "This is regular text without code block\n"
    ),
    (
        "```\n```",
        "\n"
    ),
    (
        "``` python\nprint(\"Hello, World!\")\n```",
        "print(\"Hello, World!\")\n"
    ),
])
def test_strip_markdown_fence(markdown, expected):
    assert strip_markdown_fence(markdown) == expected

def test_normalize_progress():
    assert normalize_progress(0) == 0

    for i in range(1, 1000, 10):
        assert normalize_progress(i) < 100

def test_call_with_supported_args():
    def f(a, b, c=0):
        return a + b + c

    assert call_with_supported_args(f, dict(a=1, b=2)) == 3
    assert call_with_supported_args(f, dict(a=1, b=2, c=3)) == 6
