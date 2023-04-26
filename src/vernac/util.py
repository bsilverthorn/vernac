import re
import math

def strip_markdown_fence(markdown: str) -> str:
    pattern = r"```\s*\w*\s*\n(?P<inner>.*?)```"
    match = re.search(pattern, markdown, re.DOTALL)

    if match:
        inner = match.group("inner")
    else:
        inner = markdown

    return inner.strip() + "\n"

def normalize_progress(x, scale=100, divisor=64, max_y=0.99):
    return scale * min(
        max_y,
        (1 - math.exp(-x / divisor)),
    )
