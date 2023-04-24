import re

def strip_markdown_fence(markdown: str) -> str:
    pattern = r"```\s*\w*\s*\n(?P<inner>.*?)```"
    match = re.search(pattern, markdown, re.DOTALL)

    if match:
        inner = match.group("inner")
    else:
        inner = markdown

    return inner.strip() + "\n"
