import re
import math
import inspect

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

def call_with_supported_args(func, args_dict):
    func_sig = inspect.signature(func)
    func_params = {p.name for p in func_sig.parameters.values()}
    supported_args = {k: v for k, v in args_dict.items() if k in func_params}

    return func(**supported_args)
