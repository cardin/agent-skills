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
    └── wsl-screenshot/
        ├── SKILL.md
        └── scripts/
            ├── capture.sh
            └── screenshot.ps1
```

## License

[MIT](LICENSE) © Cardin Lee
