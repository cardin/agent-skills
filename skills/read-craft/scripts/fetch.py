#!/usr/bin/env python3
"""Fetch the Markdown form of a public Craft share document.

Transport only: this module never writes to the filesystem. It resolves a public
https://<host>.craft.me/<share-id> link, downloads Craft's share JSON, and renders
it as Markdown.
"""

import argparse
import json
import re
import subprocess
import sys
from urllib.parse import urlsplit

API_TIMEOUT = "30"


def parse_url(url):
    parts = urlsplit(url)
    host = parts.hostname or ""
    share = re.fullmatch(r"/([A-Za-z0-9]+)/?", parts.path)
    if parts.scheme != "https" or not host.endswith(".craft.me") or not share or parts.port or parts.username:
        raise ValueError("Expected a public https://<host>.craft.me/<share-id> link")
    return f"https://{host}/{share[1]}", share[1]


def fetch_document(url):
    """Download and decode the Craft share JSON for a public link."""
    base, share_id = parse_url(url)
    api = base.rsplit("/", 1)[0] + "/api/share/" + share_id
    response = subprocess.run(["curl", "-fsSL", "--max-time", API_TIMEOUT, api], check=True, capture_output=True)
    return json.loads(response.stdout)


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
        raise ValueError("Empty document; nothing to render")
    return "".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="Public Craft share link")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--md", action="store_const", const="md", dest="format", help="Markdown to stdout (default)")
    output.add_argument("--json", action="store_const", const="json", dest="format", help="Markdown plus metadata as JSON")
    output.add_argument("--raw", action="store_const", const="raw", dest="format", help="Raw Craft share JSON")
    parser.set_defaults(format="md")
    args = parser.parse_args(argv)
    try:
        canonical, share_id = parse_url(args.url)
        document = fetch_document(args.url)
        if args.format == "raw":
            json.dump(document, sys.stdout)
        elif args.format == "json":
            json.dump({
                "url": canonical,
                "host": urlsplit(canonical).hostname,
                "share_id": share_id,
                "markdown": render(document),
            }, sys.stdout)
        else:
            sys.stdout.write(render(document))
        sys.stdout.write("\n")
        return 0
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as error:
        print(f"read-craft failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
