# Cursor runtime

Use this package's sibling skills and named agents. Preserve native Task, model-role rules, cloud lifecycle tools, and Cursor metadata. Do not treat Codex model identifiers as Cursor model identifiers.

For implementation tasks, apply [the hybrid execution policy](hybrid.md): Cursor builds, Codex reviews, and Codex can rescue a blocked implementation. A user's per-task native-only or different builder/reviewer instruction overrides that default. Pure explanations, planning, and questions do not launch a paid CLI review automatically.

Read the runner's `--help` and [local setup](../docs/cursor-local.md) before first use. If Codex is absent or unauthenticated, report the missing prerequisite; do not call a Cursor GPT-model Task a Codex CLI review. Do not claim the hybrid review passed when only native review ran.

A delegated review/rescue worker executes only its assigned role. It must not recursively invoke hybrid routing. Never send work to a cloud service, merge, publish, or schedule anything beyond the user's authorized scope.
