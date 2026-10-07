# agent-skills

[![skills.sh](https://skills.sh/b/cardin/agent-skills)](https://skills.sh/cardin/agent-skills)

Agent [skills](https://skills.sh) by [Cardin Lee](https://github.com/cardin).

## Install

```bash
# Install to OpenCode globally
npx skills add cardin/agent-skills --skill wsl-screenshot -g -a opencode -y

# Or pick agents interactively (Claude Code, Codex, Cursor, ...)
npx skills add cardin/agent-skills --skill wsl-screenshot
```

Preview without installing:

```bash
npx skills add cardin/agent-skills --list
```

## Skills

### `craft-to-agents`

Import a public Craft document into its own section of `AGENTS.md`, or refresh it
later using the source link recorded inside the section.

```bash
npx skills add cardin/agent-skills --skill craft-to-agents -g -a opencode -y
```

Once installed, ask your agent: "Import this Craft document into AGENTS.md: URL"
or "Refresh the Craft workflow section in AGENTS.md."

**Requirements:** Python 3.9+, `curl`, and a public `craft.me` share link.

**Behavior:** preserves unrelated/plugin sections, formats headings, paragraphs,
lists, bold, and inline code, excludes the `IGNORE` heading and everything after it,
and leaves unchanged files untouched. Failed imports do not replace existing content.

```bash
python3 <skill-dir>/scripts/sync.py "CRAFT_URL"
python3 <skill-dir>/scripts/sync.py "CRAFT_URL" --target ./AGENTS.md --block my-rules
```

The default target is `~/.config/opencode/AGENTS.md`. Existing source-linked blocks
are reused; new blocks use `craft-<share-id>`. For an older block without a source
link, use `--block` with its current name to migrate it without creating a duplicate.
Craft's share API is undocumented, so future API changes may require an update.

Run the offline tests:

```bash
python3 -m unittest discover -s skills/craft-to-agents/tests -v
```

### `wsl-screenshot`

Capture the Windows desktop from inside WSL and view the result.

The gap this fills: existing screenshot skills cover macOS, native Linux (X11), and native
Windows, but none bridge **WSL → Windows**. From WSL you cannot use `scrot`/`import`
(no Linux display) and you cannot call a `.ps1` by its Linux path, so a naive screenshot
skill fails. This one handles the bridge for you.

**Requirements**

- WSL with Windows interop enabled (`powershell.exe` reachable from bash)
- An unlocked, connected Windows desktop session (a locked session captures black)

**Usage**

Once installed, just ask your agent to look at your screen. Under the hood it runs:

```bash
bash <skill-dir>/scripts/capture.sh          # all monitors
bash <skill-dir>/scripts/capture.sh -m 2     # one monitor
bash <skill-dir>/scripts/capture.sh -w 1600  # downscale wide captures
bash <skill-dir>/scripts/capture.sh -o DIR   # custom output directory
```

It prints the image's WSL path (e.g. `/mnt/c/Users/you/AppData/Local/Temp/...png`), which
the agent opens with its image-reading tool.

**How it works**

1. `scripts/capture.sh` locates itself, converts that path with `wslpath -w`, and calls
   `powershell.exe` on `scripts/screenshot.ps1`.
2. `screenshot.ps1` captures the virtual desktop (all monitors) or a single display with
   .NET `CopyFromScreen`, opting into DPI awareness, and writes a PNG to Windows temp.
3. `capture.sh` converts the result back with `wslpath -u` and prints the WSL path.

**Notes**

- Reading `/mnt/c/...` may need an `external_directory` permission entry in
  `opencode.jsonc`. If access is denied, either add the permission or use `-o` to write to
  a directory you can already read.
- Screenshots can contain sensitive information. Capture only when the request calls for it.

**Related skills**

- [`openai/skills@screenshot`](https://skills.sh/openai/skills/screenshot) — broader and
  more polished, and the right choice on macOS, native Linux, or native Windows. It has no
  WSL support, which is why this skill exists. Both can be installed side by side; IDs
  differ (`wsl-screenshot` vs `screenshot`).

## Repository layout

```text
agent-skills/
└── skills/
    ├── craft-to-agents/
    │   ├── SKILL.md
    │   ├── scripts/
    │   │   └── sync.py
    │   └── tests/
    │       └── test_sync.py
    └── wsl-screenshot/
        ├── SKILL.md
        └── scripts/
            ├── capture.sh
            └── screenshot.ps1
```

## License

[MIT](LICENSE) © Cardin Lee
