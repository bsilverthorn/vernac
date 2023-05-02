import re
import os.path
import math
import inspect

from typing import (
    Callable,
    TypeVar,
)

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

def str_to_filename(string: str):
    str_lower = string.lower()
    spaces_replaced = re.sub(r"\s+", "_", str_lower)
    only_safe = re.sub(r"[^\w_]", "", spaces_replaced)

    return only_safe

T = TypeVar("T")

async def call_with_supported_args(func: Callable[..., T], args_dict: dict) -> T:
    func_sig = inspect.signature(func)
    func_params = {p.name for p in func_sig.parameters.values()}
    supported_args = {k: v for k, v in args_dict.items() if k in func_params}

    if inspect.iscoroutinefunction(func):
        return await func(**supported_args)
    else:
        return func(**supported_args)

def replace_ext(path, new_ext):
    (name, _) = os.path.splitext(path)

    return f"{name}.{new_ext}"
