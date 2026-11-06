---
name: living-docs-reconcile
description: "Reconcile a feature spec into authoritative living docs. Use when a feature reaches no-outstanding-tasks, when its spec content is needed in living docs before completion, or when work is being stopped. Records a disposition manifest, merges content per outcome, handles provisional markers. Named in AGENTS.md; run before opening the MR that ends a feature."
license: MIT
compatibility: Requires a project with docs/ living docs and specs/<feature>/ feature specs. No extra dependencies.
---

# living-docs-reconcile

You are reconciling a feature spec into authoritative living documents.
Living docs are canonical. The spec is a proposal that must end up merged or
explicitly dispositioned. You never edit intent to match code: discrepancies
are findings for a human, not things to smooth over.

## Inputs

- Spec folder path and outcome (`complete`, `partial`, `abandoned`)
- Current living docs — **re-read from disk; never rely on remembered state,
  including a previous partial merge's state**
- Spec decision log, task list, acceptance criteria, existing ADRs
- Git diff vs merge base, test/CI evidence, linked tracker items (read-only
  unless tracker updates are pre-approved routine ones)

## Step 0 — Verify the gate

- `complete`: verify, do not assume — acceptance criteria pass, tests/CI
  green, no open decisions, no unapproved intent changes in the diff. If any
  fail or cannot be verified, downgrade to `partial` and state why. Never
  upgrade `partial` or `abandoned` to `complete`.
- All outcomes: if you find an approved-intent change still awaiting a doc
  update outside this reconciliation, stop and report it.

## Step 1 — Build the delta inventory

Classify each spec section against current living docs:

| Spec artifact | Canonical destination     | Notes                     |
|---------------|---------------------------|---------------------------|
| spec.md       | REQUIREMENTS.md           | behaviour, criteria, IDs  |
| plan.md       | DESIGN.md + ADR.md        | architecture vs decisions |
| research.md   | ADR.md (+ DESIGN.md)      | alternatives, constraints |
| data-model.md | INTERFACES.md             | schemas                   |
| contracts/    | INTERFACES.md             | one canonical location    |
| tasks.md      | MR description or discard | execution history         |
| quickstart.md | operational docs          | only if durable           |
| checklists/   | TESTPLAN.md or discard    | verification, not contract|

Artifacts with no destination are deliberate discards recorded in the
manifest, not oversights.

Then check against code/tests, not the spec alone:

- spec claims without code/test evidence → `intended, unverified`;
- behaviour in the diff not in the spec → report, ask if intent changed;
- sections this feature partially merged that changed since → re-diff
  against current docs; living docs win by default, conflicts go to review.

## Step 2 — Draft the changes

- Rewrite in current-state prose (no task language, no "feature X will...").
- Integrate into existing sections; do not append "Feature X" subsections.
- Preserve requirement IDs; retire explicitly, never renumber.
- Promote every unrecorded decision to an ADR with rejected alternatives,
  constraints, and source. Mark unsourced rationale `unverified`; never
  invent it.
- Run a consistency pass over each affected document as a whole (stale
  statements, cross-references, retired IDs, requirement-to-test mapping).
- `partial`: merge only approved, stable content. Use the exact Provisional
  marker format from the project's AGENTS.md (fallback below if the project
  has none). Add a merge ledger in the spec so re-runs update in place
  instead of duplicating.
- `abandoned`: write the short ADR (context, options, why stopped, revisit
  conditions). Retract this feature's provisional markers (remove content +
  marker). Do not delete still-valid unmet requirements — mark them
  unmet/deferred. Scan all living docs for claims that assumed this feature.
- `complete`: finalize this feature's provisional markers (keep content,
  remove marker). Leave other features' markers untouched.

Provisional marker fallback (use the project's AGENTS.md definition when
present, this shape otherwise):

```markdown
> Provisional — feature `checkout-guest`: <what is not final>.
> See `specs/checkout-guest/spec.md`.
<!-- provisional:feature=checkout-guest -->
```

Find all markers for a feature with `rg "provisional:feature=<id>"`.

## Step 3 — Classify and route approvals

Label each edit `normative` (requirements, interfaces, criteria, decision
supersedes) or `descriptive` (narrative, clarifications). Normative edits
need the document owner's approval, not just the feature author's. List
unapproved normative edits as blocked with who must approve.

## Step 4 — Disposition manifest

One entry per spec artifact/section, into the MR description:

```text
spec.md#R-7       -> merged-to: REQUIREMENTS.md#R-12   [normative]
research.md#alt-2 -> promoted-to: ADR-018              [rejected option]
tasks.md          -> discarded: execution history
data-model.md#e9  -> retained: spec (unverified claim R-9)
```

No spec deletion while any entry is unresolved, blocked, or `unverified`
without a stated human decision.

## Step 5 — Apply, then close out

- `complete`: after docs review, delete the spec folder in a separate commit.
  Before deleting, retarget inbound links (tracker, ADRs, other specs) to
  the MR/ADR.
- `abandoned`: move the spec to the archive location; update tracker closure
  per AGENTS.md rules.
- `partial`: do not delete, do not archive.

## Guardrails

- Living docs win every conflict. When unsure, re-read; never reconstruct
  from memory of the spec or an earlier merge.
- Never delete with unresolved manifest entries, and never in the merge
  commit.
- Never invent rationale, approvals, or evidence.
- If living docs changed materially since branch base, rebase and re-run.
- Idempotent: re-running with the same outcome updates in place.
- If the gate fails, an owner is unreachable, or intent changed without
  approval, stop with a findings report.

## Manual fallback

Inventory spec artifacts against the mapping table, verify claims against
tests, promote unrecorded decisions, merge with AGENTS.md provisional markers
if partial, write the manifest into the MR description, then delete or
archive. The manifest is the requirement; the tooling is not.
