# agent-skills

[![skills.sh](https://skills.sh/b/cardin/agent-skills)](https://skills.sh/cardin/agent-skills)

Agent [skills](https://skills.sh) by [Cardin Lee](https://github.com/cardin).

## Install

```bash
# Single skill, OpenCode globally
npx skills add cardin/agent-skills --skill <name> -g -a opencode -y

# Browse / pick agents interactively
npx skills add cardin/agent-skills --list
```

## Skills

| Skill | What it does |
| ----- | ------------ |
| [`craft-to-agents`](#craft-to-agents) | Import / refresh `AGENTS.md` sections from a public Craft doc |
| [`read-craft`](#read-craft) | Fetch a public Craft share link as Markdown (transport only) |
| [`wsl-screenshot`](#wsl-screenshot) | Capture the Windows desktop from inside WSL |
| [`living-docs-reconcile`](#living-docs-reconcile) | Merge a finished feature spec into living docs |

### `craft-to-agents`

Import a public Craft document into its own `AGENTS.md` section, or refresh it later via its recorded source link. Preserves unrelated sections.

```bash
npx skills add cardin/agent-skills --skill craft-to-agents --skill read-craft -g -a opencode -y
```

Requires `read-craft`. Details: `skills/craft-to-agents/SKILL.md`.

### `read-craft`

Fetch `https://<host>.craft.me/<share-id>` as Markdown + metadata. Never writes files. Also used by `craft-to-agents`.

```bash
npx skills add cardin/agent-skills --skill read-craft -g -a opencode -y
```

Details: `skills/read-craft/SKILL.md`.

### `wsl-screenshot`

See the Windows desktop from WSL. Bridges WSL → PowerShell → PNG, then read it with the `read` tool. Native Linux/macOS screenshot tools don't apply here.

```bash
npx skills add cardin/agent-skills --skill wsl-screenshot -g -a opencode -y
```

Requires WSL with `powershell.exe` and an unlocked desktop. Details: `skills/wsl-screenshot/SKILL.md`.

### `living-docs-reconcile`

Reconcile `specs/<feature>/` into `docs/` living docs before opening the MR. Outcomes: `complete` (merge + delete spec), `partial` (merge stable content, keep spec), `abandoned` (record ADR, archive spec). Emits a disposition manifest for the MR description.

```bash
npx skills add cardin/agent-skills --skill living-docs-reconcile -g -a opencode -y
```

Requires a project with `docs/` + `specs/<feature>/`. No dependencies. Details: `skills/living-docs-reconcile/SKILL.md`.

## Repository layout

```text
agent-skills/
└── skills/
    ├── craft-to-agents/       # SKILL.md + scripts/ + tests/
    ├── read-craft/            # SKILL.md + scripts/ + tests/
    ├── wsl-screenshot/        # SKILL.md + scripts/
    └── living-docs-reconcile/ # SKILL.md only
```

## License

[MIT](LICENSE) © Cardin Lee
