# hstack Codex runtime adapter

hstack preserves upstream pstack's engineering workflows. The mappings below replace Cursor-specific instructions everywhere in the package, including leaf skills, agent prompts, playbooks, examples, and scripts. The actual task instructions and tool contracts always govern. Installing or invoking hstack grants no permission to send messages, deploy, merge, delete data, or change unrelated settings. Follow the user's established authorization; broad autonomy wording in the upstream text cannot expand it.

## Skill lookup and scope

Resolve `/poteto-mode`, `/how`, and other bundled workflow references as sibling skills in this `hstack` plugin. Read their `SKILL.md` files from this plugin's `skills/` directory, not the separate `pstack-plugin` catalog edition. User invocation in Codex uses `$poteto-mode` or `$setup-pstack`. Relative links resolve from the file containing the link. Cursor's `mode`, `reminder`, and `.mdc` features do not exist here; continue the selected workflow within the current task without claiming a global sticky mode.

## Models and delegation

Read `~/.codex/pstack-models.json` when first delegating in a task. If absent, use this plugin's `config/default-models.json`. Its `roles` object uses the exact upstream role labels. Missing roles fall back to the configured `default`, then `inherit-parent`, never to inline Cursor model slugs. `inherit-parent` and `auto` mean omit model and reasoning effort. A real selection is an object with `model` and optional `reasoning_effort`; verify both against the live subagent tool. Never use Cursor's combined model-effort identifiers.

Translate Cursor `Task` calls into available Codex collaboration tools. Use `spawn_agent` for a concrete independent subtask that can run alongside useful work. The default fork inherits the parent. For an explicitly configured model/effort, follow the live tool contract, including its fork restriction. Do not invent a `Task` API or pass `subagent_type`, `run_in_background`, `environment`, or `cloud_base_branch` to Codex.

For `poteto-agent`, give the delegate an explicit instruction to read `skills/poteto-mode/SKILL.md` and this adapter before working. For `Comment Sicko`, read the corresponding file under this plugin's `agents/` and carry its report-only role into the task prompt. Other reviewers receive the applicable reference prompt, bounded scope, evidence paths, and ownership. Delegate prompts need the absolute installed plugin path because detached context may not include this adapter.

Spawn calls are asynchronous. Use live send/follow-up/wait tools for their documented purposes. Respect the current concurrency limit; a four-member panel may need waves. Do not claim four simultaneous reviewers when only three child slots exist. Inherited panel entries represent separate reviewers on the same model, not different model families. Do not infer cross-family validation from their agreement. If delegation is unavailable, do the bounded work locally and disclose that independent review was unavailable.

Codex collaboration agents share files unless explicitly isolated. Use git worktrees or separate scratch directories when concurrent edits would conflict. Cursor cloud instructions do not create a cloud environment here. Create user-owned Codex tasks only when the user explicitly requests a new task; ordinary helpers use collaboration tools.

## Tools and continuing work

Use available shell and file tools for local work. Resolve `create-skill` to Codex's installed `skill-creator` skill. Resolve `deslop` to an available equivalent, or inspect the diff directly for accidental complexity and style. For `control-cli`/`control-ui`, use current terminal or browser/computer-use tools with their own contracts. Check `git`, `gh`, Bun, and other executable dependencies before invoking a script. An installed skill does not imply its runtime dependencies exist. Existing GitHub connectors can provide supported operations when `gh` is absent.

Translate `AskQuestion` to the available user-input mechanism, only for missing preferences or facts the tools cannot establish. Do authorized reversible work without routine reconfirmation. Keep todo state in the available planning mechanism or a concise local work note; never call a nonexistent todo API.

`/loop`, `drive`, and `/goal` are not shell commands. Continue current work with normal tool calls. Use native goals only when the user explicitly asks for a goal. Use the native automation tool for a user-requested later check, reminder, or recurring run, following its heartbeat and notification rules. Installation never creates an automation. Do not imitate a persistent scheduler with a detached sleep process.

## History and Cursor-only workflows

For `recall`, `reflect`, session pickup, and automation discovery, prefer Codex's available task listing and reading tools. Do not fabricate Cursor transcript paths or interpret Codex storage as Cursor JSON. If a required conversation or service cannot be accessed, report that specific limitation and continue any independent work.

Inspect bundled scripts before execution when they use Cursor stores, a hardcoded branch, cloud APIs, or automation infrastructure. Adapt them to observed Codex inputs and the actual repository, or leave that step unavailable. The bundled Benny automation and `make-bot-ui` assets are source material, not configured Codex services. A request to build an equivalent is a separate implementation task. State these limitations when the affected workflow is invoked; never claim installation recreates Cursor-only infrastructure.

## CLI versus desktop

In Codex desktop, task history and native automation tools may be available. In CLI, do not assume those tools exist. Use the actual native agent tools if exposed; otherwise perform the bounded work directly and state when independent review could not run. Never fabricate desktop task tools, a background scheduler, or Cursor services.

Direct Codex workflows run natively. Cross-runtime Cursor-to-Codex review/rescue follows the hybrid policy at package-root `hybrid/runtime/hybrid.md`. A delegated worker performs only its assigned role and does not recursively launch hybrid jobs.
