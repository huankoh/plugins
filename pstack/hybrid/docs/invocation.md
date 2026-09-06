# Choose hstack or pstack explicitly

hstack generates distinct skill and agent names. The original pstack source and installation keep their original names.

| Host | hstack request | Original pstack request |
| --- | --- | --- |
| Cursor | `/hstack-poteto-mode` | `/poteto-mode` |
| Codex qualified catalog (desktop and tested cloud) | `$hstack:hstack-poteto-mode` | `$pstack:poteto-mode` |
| Codex unqualified portable catalog | `$hstack-poteto-mode` | `$poteto-mode` |
| Grok Bot | Ask the hstack-configured bot to use `hstack-poteto-mode` | Use the original bot and its pstack workflow |

The same prefix applies to all 45 generated skills, including `hstack-how`, `hstack-architect`, and `hstack-setup-pstack`. Generated named agents also use the prefix. Existing model preferences remain unchanged.

The skill's own name uses hyphens: `hstack-poteto-mode`. Codex can add the package namespace in its catalog, producing `hstack:hstack-poteto-mode`; both the local native plugin and the tested cloud installation displayed that qualified name. Select the matching entry shown by the host. `hstack:poteto-mode` is not the cross-host command contract. Cursor documents `/skill-name` and requires the skill name to match its folder. [Cursor skills](https://cursor.com/docs/skills)

After selecting hstack, its runtime resolves delegated workflows and agent instructions from that package's `SKILL-MAP.json`. It must report missing instructions or host capabilities instead of substituting an original pstack skill. When a named hstack agent is unavailable, the coordinator can brief a supported generic worker with the exact bundled agent instructions.

For implementation in Cursor, hstack defaults to Cursor building and an actual Codex CLI worker reviewing. Authentication and CLI installation are separate prerequisites on the execution host. Explanations and planning do not automatically start CLI review. Direct Codex work uses its native tools. A Grok coordinator passes the hstack identity and selected package paths with each handoff.

## Make Cursor skills available automatically

The tested setup combines the [pinned GitHub marketplace installation](cursor-local.md#install-the-pinned-remote-marketplace) with personal skill export and **Sync Skills for Cloud Agents**. The namespaced package is on the distribution's review branch, not yet `main`. After building the selected source, export its skills:

```bash
.venv/bin/python pstack/hybrid/install-cursor-skills.py dist/hstack/cursor/plugins/hstack
```

The default destination is `~/.cursor/skills`. Only uniquely named hstack directories are managed. Original pstack and other personal skills stay in place. An existing unrecognized directory or local edits cause the installer to stop.

Each public skill loads its full workflow from a shared package under `hstack-poteto-mode/references/`. All dependencies travel with the exported skills. Internal workflow documents use `WORKFLOW.md` so Cursor does not discover a second set of duplicate skills inside that payload.

Enable **Settings → Agents → Context and Tools → Sync Skills for Cloud Agents** and wait for **Skills synced**. Sync applies to the personal skills directory as a whole. The recorded setup contained 47 skills: 45 hstack exports and two preserved existing styles. [Cloud skill support](https://cursor.com/help/ai-features/cloud-agents)

The [fresh cloud test](https://cursor.com/agents/bc-d843572d-c606-49ae-9ecf-c3023d85788b) then found `hstack-poteto-mode` and `hstack-setup-pstack` in its initial catalog and loaded the entrypoint, package map, and Cursor runtime without manual file paths. It selected the native plugin cache for distribution commit `66b1ac1ac6ae2c190a9ff20a9f1db28f367c4977`, built from source `bbe9d3e`. This verifies the combined setup; the evidence does not isolate personal sync as the cause of native plugin discovery.

The earlier cloud Start exporter placed 45 wrappers in project `.cursor/skills` and kept Git clean, but did not establish discovery. It remains an optional export utility, not the current cloud recipe. The [cloud guide](cursor-cloud.md) records the tested Build, normal Start command, and separate CLI/authentication preparation. Personal skill availability does not make every cloud VM ready to execute Codex.

## Verify selection

Start a fresh task and invoke only the host's hstack command with a small request. Verify that the loaded path ends in `hstack-poteto-mode/SKILL.md`, or that its portable wrapper resolves to the matching `WORKFLOW.md`. The package map and `BUILD.json` identify the source revision. An available original `poteto-mode` must remain a separate entry.

Native Codex discovery was verified on 2026-09-07: a fresh app-server found all 45 installed hstack skills alongside all 45 original personal pstack skills, with distinct names and both poteto entrypoints enabled. The probe used an empty temporary directory with no staged skills or symlinks. See the [local evidence and source revision](codex.md#verified-local-discovery).

For a coding test, also require the actual Codex job report and current-commit validation. Discovering a skill proves selection; it does not prove authentication or a completed review.
