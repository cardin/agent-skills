#!/usr/bin/env python3
"""Manage independently editable blocks in a Markdown file.

A block is delimited by `<!-- <name>:start -->` and `<!-- <name>:end -->` markers and
records the link it came from as a `Source: <url>` line, so a later run can find and
refresh it without knowing its name. This module is source-agnostic: it is told the
block name, the source link, and the replacement body, and knows nothing about Craft.
"""

import os
from pathlib import Path
import re
import tempfile

MARKER = re.compile(r"(?ms)^<!-- ([\w-]+):start -->\r?\n(.*?)^<!-- \1:end -->")
BLOCK_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*")


def find_block(text, source):
    """Return the name of the single block recording `source`, or None.

    Raises ValueError when more than one block claims the source.
    """
    matches = [name for name, body in MARKER.findall(text) if f"Source: <{source}>" in body]
    if len(matches) > 1:
        raise ValueError("Multiple blocks use this source; specify --block")
    return matches[0] if matches else None


def render(markdown, source, block_name, hint="craft-to-agents"):
    """Build the managed block text for `block_name`."""
    if not BLOCK_NAME.fullmatch(block_name):
        raise ValueError("Invalid block name; use letters, numbers, underscores, or hyphens")
    start, end = (f"<!-- {block_name}:{edge} -->" for edge in ("start", "end"))
    note = f"Source: <{source}>" + (f" (refresh with the {hint} skill)" if hint else "")
    return f"{start}\n{note}\n\n{markdown}\n{end}"


def merge(old, markdown, source, block_name, hint="craft-to-agents"):
    """Return `old` with the managed block replaced in place, or appended if absent."""
    block = render(markdown, source, block_name, hint)
    start, end = (f"<!-- {block_name}:{edge} -->" for edge in ("start", "end"))
    if start in markdown or end in markdown:
        raise ValueError("Document contains managed block markers")
    if start in old or end in old:
        if old.count(start) != 1 or old.count(end) != 1 or old.index(start) > old.index(end):
            raise ValueError("Invalid block markers; refusing to modify the file")
        new = old[:old.index(start)] + block + old[old.index(end) + len(end):]
    else:
        new = old + ("\n" if old.endswith("\n") else "\n\n" if old else "") + block + "\n"
    return new


def write(target, markdown, source, block_name, hint="craft-to-agents"):
    """Atomically replace or extend `target` with the block. Returns a status string."""
    target = Path(target).expanduser().resolve()
    old = target.read_bytes().decode("utf-8") if target.exists() else ""
    new = merge(old, markdown, source, block_name, hint)
    if new == old:
        return f"Unchanged: {target} [{block_name}]"
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=target.parent, prefix=f".{target.name}.")
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(new.encode("utf-8"))
        os.chmod(temporary, target.stat().st_mode & 0o777 if target.exists() else 0o600)
        os.replace(temporary, target)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return f"Updated: {target} [{block_name}]"
