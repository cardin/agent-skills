#!/usr/bin/env python3
"""Import a public Craft share into an independently managed Markdown block.

Transport is delegated to the `read-craft` skill; block placement is handled by
blocks.py. This script only wires the two together and knows the one Craft-specific
convention: blocks default to the name `craft-<share-id>`.
"""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

import blocks  # noqa: E402

HINT = "craft-to-agents"
READ_CRAFT_ENV = "READ_CRAFT_SCRIPT"


def locate_read_craft(override=None):
    """Find read-craft's fetch.py (explicit, env, sibling skill, then common roots)."""
    if override:
        candidates = [Path(override).expanduser()]
    else:
        candidates = []
        if os.environ.get(READ_CRAFT_ENV):
            candidates.append(Path(os.environ[READ_CRAFT_ENV]).expanduser())
        skill = Path("read-craft") / "scripts" / "fetch.py"
        candidates.append(Path(__file__).resolve().parents[2] / skill)
        roots = (Path.home() / ".agents/skills", Path.home() / ".config/opencode/skills", Path.home() / ".claude/skills")
        candidates += [root / skill for root in roots]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        f"read-craft skill not found; install it, set {READ_CRAFT_ENV}, or pass --read-craft"
    )


def read_craft(script, url):
    """Run read-craft's fetch.py and return its JSON result."""
    response = subprocess.run([sys.executable, str(script), url, "--json"], check=True, capture_output=True)
    document = json.loads(response.stdout)
    if not document["markdown"].strip():
        raise ValueError("Empty import; refusing to modify the target")
    return document


def sync(url, target, block_name=None, hint=HINT, read_craft_script=None):
    """Fetch `url` via read-craft and write it into `target`. Returns a status string."""
    document = read_craft(locate_read_craft(read_craft_script), url)
    source = document["url"]
    target = Path(target).expanduser().resolve()
    old = target.read_bytes().decode("utf-8") if target.exists() else ""
    block_name = block_name or blocks.find_block(old, source) or f"craft-{document['share_id']}"
    return blocks.write(target, document["markdown"], source, block_name, hint)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="Public Craft share link")
    parser.add_argument("--target", default="~/.config/opencode/AGENTS.md")
    parser.add_argument("--block", help="Reuse a custom or legacy managed block name")
    parser.add_argument("--hint", default=HINT, help="Skill name recorded in the refresh note")
    parser.add_argument("--read-craft", dest="read_craft_script", metavar="PATH", help="Path to read-craft's fetch.py")
    args = parser.parse_args()
    try:
        print(sync(args.url, args.target, args.block, args.hint, args.read_craft_script))
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Import failed: {error}\n")
