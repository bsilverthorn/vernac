import pytest

from vernac.util import strip_markdown_fence

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
