import pytest

from vernac.util import (
    strip_markdown_fence,
    normalize_progress,
    str_to_filename,
    call_with_supported_args,
    replace_ext,
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

@pytest.mark.parametrize("unsafe, expected", [
    ("This is a Test String", "this_is_a_test_string"),
    ("Test@#$%^&*()_+|}{[]", "test_"),
    ("    ", "_"),
])
def test_str_to_filename(unsafe, expected):
    assert str_to_filename(unsafe) == expected

@pytest.mark.asyncio
async def test_call_with_supported_args():
    def f(a, b, c=0):
        return a + b + c

    assert await call_with_supported_args(f, dict(a=1, b=2)) == 3
    assert await call_with_supported_args(f, dict(a=1, b=2, c=3)) == 6

@pytest.mark.parametrize("input_path,new_ext,expected_output", [
    ("example.txt", "pdf", "example.pdf"),
    ("path/to/file.html", "txt", "path/to/file.txt"),
    ("file_without_ext", "jpg", "file_without_ext.jpg"),
    ("file.with.dots.txt", "png", "file.with.dots.png"),
    ("", "csv", ".csv"),
])
def test_replace_ext(input_path, new_ext, expected_output):
    assert replace_ext(input_path, new_ext) == expected_output
