# Run hstack directly in Codex cloud

Use this guide for repository tasks in [Codex cloud](https://chatgpt.com/codex). This setup stages hstack for the cloud agent itself. It does not launch a separate Codex CLI worker or configure a ChatGPT Work cloud task.

## Prepare a pinned setup script

Choose a tested full commit SHA from [the hstack fork](https://github.com/huankoh/plugins). Fresh namespaced Codex cloud discovery passed at `bbe9d3e5d3f3531227e4c5d88da99a6394540bb1`. The selected revision must contain `pstack/hybrid/build.py`. Use the exact SHA throughout setup and verification.

Open [setup-codex-cloud.sh](../setup-codex-cloud.sh) from your reviewed checkout. To prepare text for the environment's setup field, prepend the selected SHA to the complete script:

```bash
HSTACK_SOURCE_SHA='<full-40-character-commit-SHA>'
```

Replace the placeholder before saving. The script rejects missing revisions, branch names, and abbreviated SHAs. When the script is already available on a host, the equivalent command is:

```bash
bash /path/to/setup-codex-cloud.sh '<full-40-character-commit-SHA>'
```

Paste the script into the environment settings instead of calling a file from the task repository. Codex can prepare its cached container from the default branch before checking out the task branch. The script fetches the pinned source into a separate checkout under `~/.local/share/hstack-codex-cloud`, so it also works before the adaptation is merged. See [Codex cloud environment setup and caching](https://learn.chatgpt.com/docs/environments/cloud-environment).

## Configure the environment

1. Open [Codex environment settings](https://chatgpt.com/codex/settings/environments).
2. Create an environment for the repository you want to test. Grant Codex access to that repository through the supported GitHub connection.
3. Use an image with Git, Python 3.9+, `venv`, and `pip`. Python 3.11+ is a suitable selection in the universal image.
4. Select manual setup and paste the complete prepared script.
5. Run the setup test. Confirm that its final JSON records the requested source revision, package path, and expected skill count.
6. Save the environment. Keep agent internet access disabled if the task needs only the included standard-library fixture.

Setup needs internet access to GitHub and the pinned Python package dependency. It creates a version-specific virtual environment and builds the complete hstack package. This setup uses no API keys, CLI login, or model overrides. Codex cloud authenticates its own agent through your account. Setup internet access and agent internet access are separate environment settings. [Codex cloud environments](https://learn.chatgpt.com/docs/environments/cloud-environment)

The script leaves the connected task repository and existing model preferences unchanged. It validates that all 45 generated skill folders carry the `hstack-` prefix and match the selected source, and requires `SKILL-MAP.json` and the runtime/configuration files. It refuses an unrelated `~/.agents/skills/hstack` directory or symlink. An earlier managed link can be updated only when it resolves into this installer's `builds/<full-SHA>/codex/plugins/hstack/skills` tree and its `BUILD.json` confirms that prior revision and runtime.

## Verify discovery before using the workflow

Start a fresh cloud task in the saved environment. Select the intended task branch explicitly. Ask the agent to record its initial native skill catalog before it reads arbitrary staged files.

The setup creates this layout:

```text
~/.local/share/hstack-codex-cloud/
├── sources/<SHA>/
├── builds/<SHA>/codex/plugins/hstack/
│   ├── skills/
│   ├── hybrid/runtime/
│   ├── config/
│   ├── SKILL-MAP.json
│   └── BUILD.json
└── setup.json

~/.agents/skills/hstack → complete package / skills
```

Read `setup.json` and `BUILD.json` to verify the source revision and fingerprint. Resolve discovered `SKILL.md` paths to the complete generated package before following their relative references. The script links only `skills/`; linking the entire package also exposes bundled automation skills outside the normal skill catalog.

Codex documents user skills under `~/.agents/skills` and supports symlinked skill folders. The cloud task must demonstrate whether its own runtime discovers those files. A local discovery result does not establish cloud support. [Codex skill discovery](https://learn.chatgpt.com/docs/build-skills)

The generated entrypoint names are `hstack-poteto-mode` and `hstack-setup-pstack`; select the entries shown by the actual cloud catalog. The tested cloud loader displayed the mode as `$hstack:hstack-poteto-mode`. A catalog qualifier does not itself establish native plugin registration: this setup stages skills through `~/.agents/skills/hstack`. The generated package permits implicit selection of its two entrypoints. The other 43 workflows retain explicit invocation policy, and the entrypoint reads its matching sibling files through `SKILL-MAP.json`. These policies make workflows available for matching requests; they do not run hstack on every task. [Codex invocation policy](https://learn.chatgpt.com/docs/build-skills)

A [fresh namespaced cloud task](https://chatgpt.com/codex/cloud/tasks/task_e_6a9d8b928a948327a1651fa41fb192b4) completed on 2026-09-07 in 3m 14s. Its initial catalog contained `hstack:hstack-poteto-mode`. It loaded the normal entrypoint at `/root/.local/share/hstack-codex-cloud/builds/bbe9d3e5d3f3531227e4c5d88da99a6394540bb1/codex/plugins/hstack/skills/hstack-poteto-mode/SKILL.md`, verified source `bbe9d3e5d3f3531227e4c5d88da99a6394540bb1` and fingerprint `dc2ec751f51e2bba5a24770ed321447aea68f1aa14e25a9d4a5b4038b9fac868`, and read the Codex adapter and package map. Mapped `hstack-poteto-mode`, `hstack-how`, `hstack-unslop`, and `hstack-poteto-agent` instructions resolved within the same package.

The connected checkout remained clean, with no file edits, model changes, authentication actions, or nested CLI execution. Native spawn was unavailable; follow-up and wait tools alone could not start an independent delegate. This pass establishes discovery and workflow selection, not an independent review or a new coding result. The [saved test environment](https://chatgpt.com/codex/cloud/settings/environment/6a9d40eecae08191a1c0f4ed6a8e4f36) fetches the complete setup script from the tested source revision.

A [historical cloud probe](https://chatgpt.com/codex/cloud/tasks/task_e_6a9d439015e8832782f23ae35e82b2d6) verified the former `hstack:poteto-mode` and `hstack:setup-pstack` catalog entries, resolved package paths, the Investigation playbook, and native independent delegation. It predates the unique `hstack-` names; its available delegation tools and review result remain separate from the current discovery-only test.

If an older package exposes only `setup-pstack`, check its invocation policy before changing discovery paths. The first cloud test used a package with all 44 other workflows marked explicit-only. Exposing `poteto-mode` resolved that catalog limitation. Absence from the initial catalog alone does not prove the loader missed a skill.

Record these outcomes separately:

- Native skill discovery means hstack appears in the cloud task's actual skill catalog.
- Explicit file loading means the agent reads the generated `skills/hstack-poteto-mode/SKILL.md` and `hybrid/runtime/codex.md` directly.
- Plugin registration requires evidence from the host's plugin mechanism. This script does not register a marketplace or install a cloud plugin.

If the runtime does not discover hstack, use explicit file loading to test the workflow and report that limitation. If the package is missing, report the setup failure. Do not present either outcome as native plugin installation.

## Run the activation fixture

Use the [activation kit](../tests/activation/README.md) from the pinned source checkout. Give the agent [the Codex prompt](../tests/activation/codex-prompt.md), with absolute paths for the package, a fresh disposable fixture, and an evidence directory outside that fixture.

Ask the agent to follow `hstack-poteto-mode`, reproduce the receipt defect, implement the fix, and run the real CLI acceptance tests. The expected baseline has four tests with three failures. The repaired sample has `paid=21.35`, `refunded=3.40`, `net=17.95`, and `settled_count=3`.

Use native Codex delegation for independent review when the cloud task exposes that capability. If delegation is unavailable, mark independent review unverified. Do not launch a nested Codex CLI to substitute for missing native tools. Direct Codex cloud execution does not test the separate Cursor-to-Codex runner connection.

Keep the connected project unchanged. Commit fixture repairs only inside its disposable Git repository. Collect the loaded package identity, base and head commits, diff, sample output, test exit codes, and actual review evidence in the cloud task's final response. Files that exist only inside the VM are not sufficient delivery evidence.

## Update the pinned version

Replace an older pasted setup script with the complete current script and update its SHA, or use a wrapper that fetches the complete script from that pinned revision. Changing only the SHA in an old script retains its old validation and upgrade behavior. Reset the environment cache before starting a fresh task. The script can rerun at the same revision and can switch an existing, verified managed link to a newly built revision. Unrelated links, directories, and inconsistent build records remain protected. To roll back, select the previous reviewed SHA and prepare a fresh cache.

No maintenance script is required for a fixed pinned package stored outside the task checkout. Repositories with their own changing dependencies may still need maintenance commands. Preserve those project-specific commands.

For a controlled installation probe, `HSTACK_CLOUD_ROOT` overrides the source and build location, and `HSTACK_CLOUD_SKILLS` overrides the skill discovery directory. Keep their defaults for normal cloud use. An arbitrary test directory does not establish native skill discovery.
