---
name: wsl-screenshot
description: "From WSL, capture the Windows desktop and look at it. Use when the user asks to see their screen, take/snap a screenshot, 'what's on my screen', 'look at my screen', or 'capture my display' while running inside WSL, or when you need visual context about the Windows host. Bridges WSL to Windows PowerShell, saves a PNG, and opens it with the Read tool. Not for native Linux or macOS desktops."
license: MIT
compatibility: Requires WSL with Windows PowerShell (powershell.exe) and an unlocked Windows desktop session.
---

# WSL Screenshot — see the user's screen

Capture what is currently on screen and look at it. From WSL, Windows PowerShell can reach
the Windows desktop, save a PNG, and the `read` tool opens it.

Supporting files sit beside this file, relative to the directory containing `SKILL.md`:

```text
wsl-screenshot/
├── SKILL.md
└── scripts/
    ├── capture.sh      # entry point (bash)
    └── screenshot.ps1  # Windows capture (PowerShell)
```

## Workflow

1. Run the capture script from the skill's base directory (OpenCode provides that base
   directory when this skill loads):

   ```bash
   bash "<skill-dir>/scripts/capture.sh"
   ```

2. It prints one line: the **WSL path** to the PNG, for example

   ```
   /mnt/c/Users/<you>/AppData/Local/Temp/opencode-screenshots/screen-20260918-210959-032.png
   ```

3. View that path with the `read` tool. This is the step that lets you see the screen —
   running the script alone shows you nothing.

   ```
   read(path="/mnt/c/.../screen-....png")
   ```

4. Answer the user's actual question about what is visible (describe the app, read the
   error, find the button). Do not just report the file path.

## Options

| Goal | Command |
|------|---------|
| All monitors (default) | `capture.sh` |
| One monitor | `capture.sh -m 1` (monitors are 1-indexed) |
| Shrink a huge capture | `capture.sh -w 1600` (max width in px, keeps aspect ratio) |
| Choose the output folder | `capture.sh -o ~/shots` |

Capture all monitors when the user does not name one. If they say "my other screen" or
"the second monitor", use `-m`; ask only if it is genuinely ambiguous.

## Notes

- By default images go to Windows temp (`%TEMP%\opencode-screenshots`), which is the
  fastest place for PowerShell to write. Override with `-o` for somewhere durable.
- Reading a `/mnt/c/...` path may require an `external_directory` permission entry for that
  path in `opencode.jsonc`. If the `read` tool is denied, either add the permission or
  re-run with `-o` pointing at a directory you are already allowed to read.
- The PNG is lossless. A full multi-monitor capture can be several MB; add `-w 1920` for a
  smaller image.
- A locked or disconnected session captures black. Say so rather than guessing at content.
- Capture only when the request calls for it. To discard old shots:
  `rm /mnt/c/Users/*/AppData/Local/Temp/opencode-screenshots/*.png`.

## Troubleshooting

- **`powershell.exe: command not found`** — not inside WSL. On native Linux use the desktop's
  own tool instead (`grim`, `gnome-screenshot`, `spectacle`, `import`).
- **Empty output / `screen capture failed`** — run the PowerShell script directly to see the
  raw error:

  ```bash
  powershell.exe -NoProfile -ExecutionPolicy Bypass \
    -File "$(wslpath -w "<skill-dir>/scripts/screenshot.ps1")"
  ```

- **Image works but you still cannot see it** — you skipped step 3. Call `read` on the
  printed path.
