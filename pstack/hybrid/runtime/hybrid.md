# hstack hybrid execution policy

Execution backend and model selection are independent. Preserve existing role preferences. The CLI runner omits model flags unless the caller explicitly supplies a Codex model. Omitting flags uses the CLI's configured default, which may differ from Cursor's current model.

Keep the selected stack explicit across hosts. A Cursor or Grok coordinator assigns `hstack-poteto-mode` and supplies the destination host's absolute hstack entrypoint and runtime adapter paths. A local path alone does not activate a remote workflow. The receiving agent verifies those files before work and resolves siblings through that package's `SKILL-MAP.json`. Missing hstack files or credentials produce a specific setup failure; they never authorize fallback to upstream pstack or an unrelated native model. Codex review/rescue workers receive only their bounded role and do not restart the full mode.

## Roles and handoff

1. Cursor implements on its own branch. Finish or checkpoint changes as a commit; record the original base and resulting head SHA. Include acceptance checks and the bounded request in a JSON task file. Local file pointers do not transfer to another VM.
2. Invoke `runner.py submit --role review --repo <checkout> --base <original-sha> --head <cursor-sha> --key <stable-task-key> --task <json-file>`. The runner creates its own detached checkout. Poll `status` and read `result`; do not submit again with a new key after an uncertain response.
3. Accept a review only when process status is succeeded, the independent verification state is passed, and `validate <id> --head <current-sha>` succeeds. Review is report-only. A changed head requires another review.
4. Repair blocking findings in Cursor. After two attempts repeat the same failing acceptance check, or Cursor explicitly reports a code blocker, offer the preserved attempt to Codex rescue under the already-authorized task scope. Stop Cursor's writer and verify its stop before handoff. Save dirty work as a checkpoint commit first; never imply uncommitted edits transferred.
5. Submit `--role rescue --writer-stopped` with the same original base and the checkpoint head, a new stable rescue key, the failure evidence, and acceptance commands. Codex works in a new checkout. The runner collects a binary patch including untracked, non-ignored files; it never applies that patch to the source checkout or pushes it automatically.
6. Cursor independently reviews the rescue patch, applies it only to the intended clean checkpoint checkout, reruns checks, and commits the accepted result. Subsequent review is keyed to that final SHA. A clean exit by the rescuer is not independent approval.

Default limits: one active Codex job per source repository, 30 minutes per job, one rescue attempt per task. Authentication, quota, missing tools and denied permissions are operational blockers, not invitations to bypass controls or switch billing. A timed-out or interrupted job needs its existing results inspected before retrying. The runner does not watch Cursor or decide whether its writer stopped; the coordinator owns these transitions.

The same runner works on a Mac, Linux bot VM, or Cursor VM. It executes on the machine where invoked. It does not forward jobs to another host. Before a disposable VM ends, collect the job report, verification results, and patch through the host's supported artifact channel. Never copy the whole state directory because logs may contain private task data.
