# hstack verification record

Upstream baseline: `93b00b89ef425a9c1bac0d0b317dfc49c930ac99`, pstack 0.14.8.

## Current namespace and discovery checks: 2026-09-07

The current runtime source is `bbe9d3e5d3f3531227e4c5d88da99a6394540bb1`,
with fingerprint
`dc2ec751f51e2bba5a24770ed321447aea68f1aa14e25a9d4a5b4038b9fac868`.
Distribution commit `66b1ac1ac6ae2c190a9ff20a9f1db28f367c4977` packages that
source. Both runtimes contain 45 distinctly named `hstack-` skills, two
`hstack-` agents, and a complete `SKILL-MAP.json`. The canonical pstack skill
and agent trees remain unchanged.

The [current source CI run](https://github.com/huankoh/plugins/actions/runs/34042006313)
passed 48 Python tests, 52 upstream tests, and the strict TypeScript check.
Namespace tests cover unique names, exact mapped files, nested links, preserved
source URLs, discoverable entrypoints, and the other 43 explicit-only workflows.
Installer and activation tests cover preserved personal files, refused local
edits, rollback after copy failure, tracked-skill protection, and repeat runs.

| Host | Current observed result | What this establishes |
| --- | --- | --- |
| Codex local native plugin | A fresh native catalog found all 45 hstack skills alongside all 45 original personal pstack skills. Its distinct entries include `$hstack:hstack-poteto-mode` and `$pstack:poteto-mode`. | Native discovery and coexistence. Unqualified catalogs use `$hstack-poteto-mode`; see the [local discovery record](codex.md#verified-local-discovery). |
| Cursor local | Distribution `66b1ac1` exposed 45 skills and two agents. `/hstack-poteto-mode` was found in the native catalog and read normally. | Local selection of the renamed package. This read-only probe performed no Codex authentication or review job. |
| Cursor cloud | A [fresh task](https://cursor.com/agents/bc-d843572d-c606-49ae-9ecf-c3023d85788b) initially listed both `hstack-poteto-mode` and `hstack-setup-pstack`, then loaded source `bbe9d3e` through its native plugin cache. | Automatic native entrypoint discovery in this tested cloud configuration, without an explicit staged-file loading instruction. |
| Codex cloud | A [fresh task](https://chatgpt.com/codex/cloud/tasks/task_e_6a9d8b928a948327a1651fa41fb192b4) initially listed `hstack:hstack-poteto-mode`, then loaded the namespaced entrypoint, Codex adapter, and package map at source `bbe9d3e`. | Native catalog discovery and same-package selection. Native spawn was unavailable, so this run does not claim an independent delegate review. |
| Grok Bot | The separate Dr. EggBot (hstack) is pinned to `bbe9d3e` and passed 21 namespace, exact-identity, and preservation checks. | Bot configuration and scoped routing checks. No Grok-side Codex login or execution has been verified. |

The successful Cursor cloud task resolved hstack from its native plugin cache
under `cache/hstack/61205765/66b1ac1...`, checked the recorded source and
fingerprint, and read the Cursor adapter and package map. It selected
`hstack-how` and `hstack-unslop` from that same package. The connected Git
checkout remained clean. The task performed no authentication, Codex job, or
application change, so it establishes discovery and same-package workflow
selection rather than a new end-to-end coding review.

That cloud run followed GitHub marketplace installation and enabling personal
skill sync after exporting 45 hstack skills. The personal directory contained
47 skills in total. The observed load path was the native plugin cache, not the
personal-skill export. These settings changed together, so the result does not
isolate which setting enabled discovery. Two earlier Start-script attempts
exported 45 locally ignored project skills but did not establish initial native
poteto discovery. Do not present that startup-export route as independently
verified by the later native-plugin result.

The fresh Codex cloud task completed in 3m 14s and resolved its normal entrypoint
under `/root/.local/share/hstack-codex-cloud/builds/bbe9d3e5d3f3531227e4c5d88da99a6394540bb1/codex/plugins/hstack/skills/hstack-poteto-mode/SKILL.md`.
It verified the current source and fingerprint above, then resolved the mapped
`hstack-poteto-mode`, `hstack-how`, `hstack-unslop`, and `hstack-poteto-agent`
instructions within that package. Git remained clean; no files, models, or
authentication settings were changed, and no nested CLI ran. The task exposed
follow-up and wait tools but no native spawn operation, so it did not perform
independent delegation. See [the Codex cloud record](codex-cloud.md#verify-discovery-before-using-the-workflow).

An automated local simulation also exercised the new Codex cloud setup script
against an older managed build containing unprefixed hstack skills. Upgrade and
repeat execution passed: the discovery symlink selected the new prefixed skills,
and the old build and original pstack files remained intact. This is local
upgrade validation; the live discovery result is recorded separately above. Updating an existing cloud
environment requires the complete current setup script as well as its pinned
SHA; see [the cloud upgrade procedure](codex-cloud.md#update-the-pinned-version).

Dr. EggBot's corrected private namespace record at `bbe9d3e` passed all 21 checks,
including package mapping, literal Codex command identities, and refusing an
upstream-pstack substitute when hstack is missing. The downloaded live entry
skill matched the package pin and same-package routing contract. Verification
caught shell interpolation that removed dollar signs from the pin's JSON
identities; the corrected record now passes exact string-equality checks. The 14-file preservation manifest for the original bots and
skills passed, the model-rule hash remained unchanged, and both copied
healthcheck routines remained paused. These are configuration checks; they do
not establish a Grok-to-Codex coding handoff.

## Historical activation evidence: 2026-09-06

The following tests record the earlier runtime versions and unprefixed hstack
entrypoints named in each run. Their successful coding, review, and
authentication results remain useful evidence for those versions. They do not
by themselves verify the current renamed installation or change the current
host results above.

### Local checks

- 32 Python package/runner/installer/auth-bootstrap tests passed on macOS with Python 3.9. Tests used an explicit CLI double for failure, cancellation, timeouts, duplicate keys, interrupted records, checkout ownership, patch collection and stale-review rejection. Installer tests covered repeat/update Git fetches, preservation of local changes, and failed-copy recovery. Auth tests covered private permissions, symlink and repository-path refusal, atomic concurrent restoration, preservation of refreshed credentials, and removal of the seed from real supervisor, Git and acceptance-check processes.
- Both generated packages preserved all 45 skills and 18 inherited role defaults. Codex entrypoint discovery and its invocation-policy adjustment are recorded below.
- The generated Codex package passed the native plugin-creator validator. Native app-server discovery found all 45 then-current skill names with no errors in a disposable workspace; `plugin/read` resolved the generated marketplace/package without installation.
- Existing pstack orchestration/watch-pr tests: 52 passed, 0 failed, with Bun 1.3.10. The existing strict TypeScript check passed.
- Python syntax compilation and shell syntax checks passed.

### Live CLI checks

Codex CLI 0.153.3 used the existing ChatGPT subscription and its configured default model. A real rescue changed subtraction to addition in a disposable fixture, preserved the source checkout and returned a collected patch. The parent applied that patch after inspection and reran its test. A separate real Codex review passed without changing files, and `validate --head HEAD` accepted the exact resulting commit. See [sanitized fixture evidence](../examples/verification-results.json).

The first live rescue returned completion notes as findings, so verification correctly remained failed. The report schema and prompt now explicitly reserve findings for unresolved blocking issues; the revised rescue and independent review passed. Automated fixture tests must not be confused with a real Cursor agent run.

### Cursor local activation

The initial Cursor installation exposed all 45 generated hstack skills.
A real Cursor task loaded hstack poteto-mode, reproduced the receipt fixture's
three failures, fixed the application and committed
`294d0108e6656dd47ff13c560ce1fc4d219691d6` from baseline
`725731a6f6a56b2549d90dd180f9635741c68b87`. Model preferences stayed inherited.

The first actual Codex review, job `6b781e7befc375f955e3d92c001bf587`, reported
blocked because its read-only sandbox could not create temporary CSV files.
The runner's acceptance suite passed, but the blocked report correctly prevented
acceptance. Commit `0c7719435557009a0e84e787075ad79ded08ae1c` clarified the
division: reviewers perform read-only checks; the runner executes supplied checks
that require temporary files. The sandbox and acceptance tests were preserved.

Cursor retried as job `c3ec145487e2f9a000a15a97b1a4fc96`. The reviewer executed
eight real CLI probes, returned `pass` with no findings, and left an empty patch.
The runner and an independent host check each passed all four acceptance tests.
Source snapshots matched before and after, the checkout remained clean, and
`validate --head HEAD` accepted the current commit. Both attempt records were
retained; a successful process alone was not treated as successful verification.

A later UI recheck found a Git-fetch error when importing the generated folder.
The local installer now publishes a stable Git marketplace and preserves prior
commits for Cursor's cached fetches. It stages both incoming trees before touching
an installation; a regression proves failed copies preserve the old checkout and
allow retry. The stable marketplace commit
`0033863ff097f08068f06c73338721715bfeec3e` was installed through Cursor's native UI,
with the temporary development symlink removed.

The fresh h3 task recorded the catalog before searching files. Only hstack's
`setup-pstack` had a native skill `fullPath`; the installation overlay listed all
45 skill names and two agents. Poteto-mode was explicitly read from the installed
native cache. Thus registered plugin/cache activation is verified, while this
run does not establish a native catalog path for every workflow.

The cached runner launched Codex job `da97c1c991a9f1258e59bc0e59aee77e` using
package source `e35ef95c149bd2a45776779a11da7e0f68366a2c`. Seven read-only
scenarios plus the sample CLI passed, the review returned `pass` with no findings,
and the runner and independent host each passed all four tests. The original
checkout remained unchanged and clean; the review patch was empty and
`validate --head HEAD` passed for the same fixture commit.

Cursor's cache omits some source assets. Core poteto-mode/review dependencies are
present. Benny setup from that cache lacks templates and setup/reproduction files;
the Codex Comment Sicko translation also expects an omitted agent source file.
The full managed marketplace retains these assets. Native Cursor's two registered
agents are separate from that Codex file-reading path.

### Codex cloud activation

The [first cloud task](https://chatgpt.com/codex/cloud/tasks/task_e_6a9d411342dc832795cbd7e87f9779bc)
used source `2709ca7b8aea576ce28b80c2d04df046d772407d`. It loaded generated
hstack skill/runtime files explicitly because the initial native catalog exposed
only `hstack:setup-pstack`. It reproduced the three fixture failures, committed a
bounded fix at `334dcd9960ae213a46bf3beb39451e7e08f7905a`, passed all four tests,
and completed an independent native Codex delegate review without reviewer edits
or findings. The connected project remained unchanged. This established the
workflow, but that run did not establish native poteto-mode discovery.

A [fresh invocation-policy probe](https://chatgpt.com/codex/cloud/tasks/task_e_6a9d439015e8832782f23ae35e82b2d6)
then changed only generated poteto-mode's `allow_implicit_invocation` from false
to true on that source version. Its initial native catalog exposed
`hstack:poteto-mode` and `hstack:setup-pstack`; the task loaded the native skill
path and Investigation playbook and used native collaboration for independent
verification without edits. The generated Codex package then encoded that
entrypoint policy. Build checks confirmed the two then-current implicit entries,
preserved the other 43 explicit-only policies, and passed the native plugin
validator. Canonical Cursor skills remained unchanged.

A [committed-package cloud run](https://chatgpt.com/codex/cloud/tasks/task_e_6a9d45f216908327a5dc396b7ea51a80)
used `e35ef95c149bd2a45776779a11da7e0f68366a2c` with the durable entrypoint
policy. Its initial native catalog exposed `hstack:poteto-mode` and
`hstack:setup-pstack`. It repaired the same baseline fixture at
`e7248c997954954a2e439d624665e98846768ba7`; all four tests passed, sample net
was 17.95, and both the fixture and connected project remained clean. This task
exposed follow-up/wait operations but no native spawn operation, so independent
review was **unverified in this run**. The earlier tasks' successful delegate
reviews remain separate evidence. Native collaboration availability varied by
task and must be checked at runtime.

### Linux and host validation

The `hstack` GitHub Actions job runs package/runner tests, upstream tests/typecheck, and a clean Ubuntu CLI installation/version check twice without credentials. The [first clean Ubuntu run](https://github.com/huankoh/plugins/actions/runs/34019930483), under the previous `pstack hybrid` job name, passed every step, including both CLI installation invocations. Subsequent PR checks validate later changes.

An initial Cursor cloud VM installed Codex CLI, staged hstack and passed all four
receipt-fixture tests. The reusable **hstack activation** environment
`b0780509-a9dd-11f1-b532-320a589b8025` initially completed Build
`bld-20260906-d9b92096-8562-458c-81c1-4921040093d3`.

A [fresh cloud task](https://cursor.com/agents/bc-bdcfc8e2-6f11-4f67-a29d-db8c9533df60)
selected that environment and cold-booted from the saved Build. It verified staged
source `e35ef95c149bd2a45776779a11da7e0f68366a2c`, fingerprint
`8caa1fe2cf724fc196bc79c104fb83a1b773d7e9f8ec11f0dac37bf055074964`, and Codex CLI
0.153.3 automatically resolved from the installer's private prefix. Its initial
catalog exposed only upstream pstack setup from `cursor-public/9717366` at
`7314f723a487ec406b6369fe5865ba034cfed166`; hstack was not natively discovered.
The task explicitly loaded staged poteto-mode and its Cursor adapter.

Saved-Build reuse, package staging and binary readiness were verified before
authentication. The user then authorized device login in that VM. The doctor
reported `auth: chatgpt` and `ready: true`, and a real nested review passed.
Handoff `hstack-activation-review-20260906`, worker
`36e19476b378cd8cf509213ae37ffb20`, reviewed fixture commit
`c4fa19a3b5dd7ea88f31d391b6fb9a9ce1656ead`. Codex returned `pass` with no
findings, the parent ran all four acceptance tests successfully, source snapshots
matched, and current-HEAD validation passed. No credential-bearing Build was made.
Native hstack cloud discovery remained unresolved in that run. The later
2026-09-07 discovery result is recorded separately above.

Commit `1447b237746e9ea58525a3b3209b5e8a4c5f20b1` adds runtime-secret bootstrap
and isolated auth-home selection. Its [CI run](https://github.com/huankoh/plugins/actions/runs/34033410467)
passed. Cold restore and repeat preservation also passed with a test CLI; these
checks do not themselves establish server authentication. The documented static
seed does not provide credential write-back or exclusive ownership across VMs.

A [fresh unattended-authentication task](https://cursor.com/agents/bc-9e37244a-77fc-48b9-b18c-858f26295c2b)
then booted from the environment's new active Build
`bld-20260906-56da8234-7e35-41b0-b5b2-1f221b191274`, with source
`1447b237746e9ea58525a3b3209b5e8a4c5f20b1` and fingerprint
`aa26de2dc500267b3cee8f047f5cee045f634f0268eb0b4e342ac99186e0c0f0`.
The runtime Start restored `HSTACK_CODEX_AUTH_JSON`, saved as an Environment
Runtime Secret, into the private auth cache. The auth file was mode `0600`; doctor
reported `auth: chatgpt` and `ready: true` before any manual login or restoration.
No manually exported `CODEX_HOME` or binary override, API-key fallback, or model
override was used.

Native poteto-mode remained absent, so the task explicitly loaded the staged
skill and Cursor adapter. It reproduced three failures, fixed the fixture, and
submitted handoff `hstack-unattended-auth-20260906`, worker
`f49fe65a58b411338f4d776dece3b136`. Codex reviewed HEAD
`f2d1218c2aec99c7f7f799eb2355407a9df44364` and returned `pass` with no findings.
The parent passed all four acceptance tests; the source snapshot was unchanged,
the fixture and connected repository stayed clean, and current-HEAD validation
returned true. This verifies server authentication after automatic secret startup
on one fresh VM. It does not establish repeated or concurrent fresh-VM token
renewal. The refreshed cache remains on that VM, and no authenticated snapshot
was created. See the [sanitized observed-UI evidence](../examples/cursor-cloud-runtime-secret-verification.json).
At the end of that test, the environment remained pinned to the tested runtime
commit. Later evidence-only documentation commits did not require a new Build.

A GitHub marketplace experiment published the identical tested package on fork
branch `hstack-cursor` at `0033863ff097f08068f06c73338721715bfeec3e`. The tested
import UI ignored the `/tree/hstack-cursor` selection and imported the
default marketplace instead. That experimental registration was removed; the
verified local hstack installation remained active. That experiment did not
establish native hstack cloud registration.

Grok Bot was outside those earlier activation checks. Its later Dr. EggBot
configuration and preservation checks are recorded in the current section;
Grok-side Codex authentication and execution remain unverified.
