---
name: setup-pstack
description: Configure pstack model roles in Codex. Use for setup-pstack, configure pstack models, or changing pstack model choices.
---

# Set up pstack in Codex

Read [the Codex runtime adapter](../../references/codex-runtime.md). This native setup replaces the upstream Cursor rule workflow.

For a request only to inspect or show the current models, read and display the effective configuration, then stop without writing files.

1. Read `~/.codex/pstack-models.json` if it exists. Otherwise use [the bundled defaults](../../config/default-models.json). Every scalar role defaults to `inherit-parent`; panel lists preserve the upstream panel count, with each entry inheriting the parent model.
2. Show the effective role mapping if the user asks to inspect or customize it. For initial setup without a model preference, use the inherited defaults. Do not ask for confirmation of those reversible defaults. Preserve existing preferences on a setup rerun unless the user asks to change them.
3. For requested routing changes, use only real model identifiers offered by the current subagent tool. Keep model and reasoning effort separate. A real model choice is an object such as `{"model": "<verified model>", "reasoning_effort": "<verified effort>"}`; omit the effort if no preference was requested. `inherit-parent` and `auto` are aliases meaning omit both model and reasoning effort. Panels are lists of aliases or model objects. Never copy Cursor's combined model-effort slugs.
4. Write the complete JSON with `version`, `default`, and `roles` to `~/.codex/pstack-models.json`. Use exactly the role keys from the bundled defaults. Read it back, validate every role and panel, and report the effective changes. This file is loaded by pstack when invoked; it does not change the model of unrelated Codex tasks.
5. Tell the user to open a new Codex task after installation and invoke `$poteto-mode` with their engineering request. They can invoke `$setup-pstack` later to change routing. Project-specific verification harnesses are created when a real project task calls for one.
