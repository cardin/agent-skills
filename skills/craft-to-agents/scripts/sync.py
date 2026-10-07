#!/usr/bin/env python3
"""Import a public Craft share into an independently managed AGENTS.md block."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from urllib.parse import urlsplit


def parse_url(url):
    parts = urlsplit(url)
    host = parts.hostname or ""
    share = re.fullmatch(r"/([A-Za-z0-9]+)/?", parts.path)
    if parts.scheme != "https" or not host.endswith(".craft.me") or not share or parts.port or parts.username:
        raise ValueError("Expected a public https://<host>.craft.me/<share-id> link")
    return f"https://{host}/{share[1]}", share[1]


def render(document):
    lines = []
    previous_list = None
    for block in document["blocks"]:
        if not block["content"].strip():
            continue
        style = json.loads(block["style"])
        heading = style.get("textStyle")
        if heading in ("title", "subtitle", "heading") and block["content"].strip() == "IGNORE":
            break
        prefix = {"title": "# ", "subtitle": "## ", "heading": "### "}.get(heading, "")
        if style.get("listStyle") == "bullet":
            prefix = "- "
        elif style.get("listStyle") == "numbered":
            prefix = str(style.get("userDefinedListNumber", 1)) + ". "
        text = block["content"].encode("utf-16-le")
        runs = [r for r in style.get("_runAttributes", []) if r.get("isCode") or r.get("isBold")]
        for run in sorted(runs, key=lambda r: r["range"][0], reverse=True):
            offset, length = (n * 2 for n in run["range"])
            span = text[offset:offset + length].decode("utf-16-le")
            if run.get("isCode"):
                fence = "`" * (1 + max(map(len, re.findall(r"`+", span)), default=0))
                pad = " " if span.startswith("`") or span.endswith("`") or (span.startswith(" ") and span.endswith(" ") and span.strip()) else ""
            else:
                fence, pad = "**", ""
            text = text[:offset] + (fence + pad + span + pad + fence).encode("utf-16-le") + text[offset + length:]
        list_style = style.get("listStyle")
        separator = "\n" if list_style in ("bullet", "numbered") and list_style == previous_list else "\n\n"
        lines.append((separator if lines else "") + prefix + text.decode("utf-16-le").rstrip())
        previous_list = list_style
    if not lines:
        raise ValueError("Empty import; refusing to modify AGENTS.md")
    return "".join(lines)


def merge(old, markdown, url, share_id, block_name=None):
    if block_name is None:
        blocks = re.findall(r"(?ms)^<!-- ([\w-]+):start -->\r?\n(.*?)^<!-- \1:end -->", old)
        matches = [name for name, body in blocks if f"Source: <{url}>" in body]
        if len(matches) > 1:
            raise ValueError("Multiple blocks use this source; specify --block")
        block_name = matches[0] if matches else f"craft-{share_id}"
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", block_name):
        raise ValueError("Invalid block name; use letters, numbers, underscores, or hyphens")
    start, end = (f"<!-- {block_name}:{edge} -->" for edge in ("start", "end"))
    block = f"{start}\nSource: <{url}> (refresh with the craft-to-agents skill)\n\n{markdown}\n{end}"
    if start in markdown or end in markdown:
        raise ValueError("Document contains managed block markers")
    if start in old or end in old:
        if old.count(start) != 1 or old.count(end) != 1 or old.index(start) > old.index(end):
            raise ValueError("Invalid block markers; refusing to modify AGENTS.md")
        new = old[:old.index(start)] + block + old[old.index(end) + len(end):]
    else:
        new = old + ("\n" if old.endswith("\n") else "\n\n" if old else "") + block + "\n"
    return new, block_name


def sync(url, target, block_name=None):
    url, share_id = parse_url(url)
    api = url.rsplit("/", 1)[0] + "/api/share/" + share_id
    response = subprocess.run(["curl", "-fsSL", "--max-time", "30", api], check=True, capture_output=True)
    markdown = render(json.loads(response.stdout))
    target = Path(target).expanduser().resolve()
    old = target.read_bytes().decode("utf-8") if target.exists() else ""
    new, block_name = merge(old, markdown, url, share_id, block_name)
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="Public Craft share link")
    parser.add_argument("--target", default="~/.config/opencode/AGENTS.md")
    parser.add_argument("--block", help="Reuse a custom or legacy managed block name")
    args = parser.parse_args()
    try:
        print(sync(args.url, args.target, args.block))
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Import failed: {error}\n")
