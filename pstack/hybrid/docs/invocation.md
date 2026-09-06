# Choose hstack or pstack explicitly

hstack generates distinct skill and agent names. The original pstack source and installation keep their original names.

| Host | hstack request | Original pstack request |
| --- | --- | --- |
| Cursor | `/hstack-poteto-mode` | `/poteto-mode` |
| Codex native plugin | `$hstack:hstack-poteto-mode` | `$pstack:poteto-mode` |
| Codex portable skills | `$hstack-poteto-mode` | `$poteto-mode` |
| Grok Bot | Ask the hstack-configured bot to use `hstack-poteto-mode` | Use the original bot and its pstack workflow |

The same prefix applies to all 45 generated skills, including `hstack-how`, `hstack-architect`, and `hstack-setup-pstack`. Generated named agents also use the prefix. Existing model preferences remain unchanged.

The portable skill name uses hyphens. Codex's native plugin catalog adds the plugin name to the frontmatter name, producing `hstack:hstack-poteto-mode`. A staged portable skill keeps `hstack-poteto-mode`. Select the matching entry shown by the host; `hstack:poteto-mode` is not the cross-host command contract. Cursor documents `/skill-name` and requires the skill name to match its folder. [Cursor skills](https://cursor.com/docs/skills)

After selecting hstack, its runtime resolves delegated workflows and agent instructions from that package's `SKILL-MAP.json`. It must report missing instructions or host capabilities instead of substituting an original pstack skill. When a named hstack agent is unavailable, the coordinator can brief a supported generic worker with the exact bundled agent instructions.

For implementation in Cursor, hstack defaults to Cursor building and an actual Codex CLI worker reviewing. Authentication and CLI installation are separate prerequisites on the execution host. Explanations and planning do not automatically start CLI review. Direct Codex work uses its native tools. A Grok coordinator passes the hstack identity and selected package paths with each handoff.

## Make Cursor skills available automatically

The portable installer exports the generated package into Cursor's supported skill directory:

```bash
python3 pstack/hybrid/install-cursor-skills.py dist/hstack/cursor/plugins/hstack
```

The default destination is `~/.cursor/skills`. Only uniquely named hstack directories are managed. Original pstack and other personal skills stay in place. An existing unrecognized directory or local edits cause the installer to stop.

Each public skill loads its full workflow from a shared package under `hstack-poteto-mode/references/`. All dependencies travel with the exported skills. Internal workflow documents use `WORKFLOW.md` so Cursor does not discover a second set of duplicate skills inside that payload.

For a repository-contained installation, pass `--destination /absolute/repository/.cursor/skills` and include the exported files in the repository. Cursor documents repository skills as available to Cloud Agents. Personal skill sync is another supported route when **Settings → Agents → Context and Tools → Sync Skills for Cloud Agents** is available and enabled. Syncing personal skills applies to that directory as a whole. [Cloud skill support](https://cursor.com/help/ai-features/cloud-agents)

The hstack cloud startup also supports exporting the selected package into the connected repository before the agent begins. It excludes only those generated directories through that repository's local Git metadata, keeping them out of application commits. The [cloud setup guide](cursor-cloud.md) records which automatic discovery route has been tested.

Cursor support has acknowledged cloud plugin-loading failures and separate duplicate-name resolution issues. The supported skill directories and distinct names address those two problems independently. Native plugin registration remains a separate test. [Cloud plugin report](https://forum.cursor.com/t/plugins-pstack-not-loading-in-cloud-environments/169740), [duplicate-name report](https://forum.cursor.com/t/workspace-skill-resolution-issue-with-identical-skill-names/162287)

## Verify selection

Start a fresh task and invoke only the host's hstack command with a small request. Verify that the loaded path ends in `hstack-poteto-mode/SKILL.md`, or that its portable wrapper resolves to the matching `WORKFLOW.md`. The package map and `BUILD.json` identify the source revision. An available original `poteto-mode` must remain a separate entry.

Native Codex discovery was verified on 2026-09-07: a fresh app-server found all 45 installed hstack skills alongside all 45 original personal pstack skills, with distinct names and both poteto entrypoints enabled. The probe used an empty temporary directory with no staged skills or symlinks. See the [local evidence and source revision](codex.md#verified-local-discovery).

For a coding test, also require the actual Codex job report and current-commit validation. Discovering a skill proves selection; it does not prove authentication or a completed review.
