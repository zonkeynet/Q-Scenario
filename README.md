# Q-Scenario community catalog

Field workflows and Action Forge tools for Q-P1NG. The catalog contains **30 scenarios and 33 tools**. This includes the original 37 examples and the new **Field Kit: 12 scenarios and 14 tools** for the Linux Sandbox tool packs. Q-P1NG retains three scenarios and three tools for first use without a network.

Start with the [Field Kit guide](docs/FIELD_KIT.md): required packages, local input files, manual review steps, and event/condition/action examples. Field Kit requires **Pro 1.0.174 (app code 175)** or newer; existing examples remain available from app code 172. No app update is needed if you already have 1.0.174: refresh the catalog explicitly through Tor.

The [validation report](docs/FIELD_KIT_TESTING.md) describes the checks on Android 11 and Android 17, including script policy, local commands and manual workflows.

## In Q-P1NG

Open **Q-Scenario / Action Forge → Community marketplace → Refresh catalog via Tor**. Search or filter, download one package, inspect its full JSON, then import. Scenarios are disabled. Downloaded tools remain disabled until **Enable after review** in Action Forge; execution still requires confirmation and the existing sandbox, target and network controls. Existing tools are not overwritten. Scenario imports create a new disabled copy.

Reading and downloading require no GitHub account. The app uses its running embedded Tor SOCKS endpoint, with remote DNS, circuit isolation, timeouts, strict size limits, no cookies, no disk HTTP cache, and no direct fallback. Opening the marketplace only reads a previously downloaded catalog from private app storage. Refresh is explicit. Each package is checked against the catalog's SHA-256, byte count, identity and schema.

SHA-256 detects mismatches with the selected catalog; it is not an independent publisher signature. Trust in the catalog currently rests on HTTPS, this repository and human review. A compromised maintainer account could replace both catalog and package. Never assume structural validation proves a script harmless.

GitHub is centralized and subject to its own availability, limits and policies. Public hosting and Actions remove the need for a Q-P1NG VPS for this catalog; they are not a guarantee of unlimited free capacity or anonymity. Existing encrypted chat sharing remains available for distributing workflows directly between contacts, including offline transports supported by Q-P1NG.

## Contribute from the app

1. Create and save a scenario/tool locally. Select **Publish to community** in the marketplace.
2. Review the complete package. Remove keys, credentials, contact identifiers, onion addresses, locations, incident details and any other private data. The selected GitHub account will be publicly associated with the issue.
3. Supply a dedicated GitHub token that can create an issue in this repository. The app does not persist the token. There is no browser OAuth flow: a normal Android Custom Tab would not inherit the app's Tor proxy.
4. Confirm publication and submit over Tor. An unconfirmed network response might still mean GitHub accepted the issue; inspect existing submissions before retrying.
5. A maintainer applies `marketplace-submission` after initial triage. The trusted workflow validates the JSON and opens a **draft PR** containing only the package and updated index. Scripts are never executed during this operation. Human review and merge publish the entry. No auto-merge.

An exported package must be your work or have a license compatible with this repository. Contributions are provided under the repository's MIT license. GitHub account identity is not hidden by Tor. Direct encrypted sharing is the account-free alternative.

## Maintainer setup

- Enable Issues and Actions. Create the `marketplace-submission` label.
- In Settings → Actions → General → Workflow permissions, enable **Allow GitHub Actions to create and approve pull requests**. The workflow only creates draft PRs; it never approves them.
- Protect `main`: require a human review and the catalog validation check. Require code-owner review for workflow changes. Do not approve a PR solely because its schema passed.
- After reviewing a bot draft, mark it **Ready for review** to trigger validation. GitHub suppresses automatic workflow cascades for PRs created with `GITHUB_TOKEN`; this explicit human event runs the check before merge. If a temporary error occurs after branch creation, reapply the label to retry the same proposal safely.
- Inspect every script, destination, permission and destructive operation. Test in an isolated profile with fictitious data. Reject secrets and misleading risk labels.
- For existing IDs, increment `version`. Updates must not reduce safety controls. The app never silently replaces installed user work.

```sh
python -m unittest discover -s tests -v
python scripts/catalog.py
python scripts/catalog.py --check
```

The format is strict JSON (not executable YAML), maximum 256 KiB per package/index, maximum 500 catalog entries, nesting depth 32. Paths are derived from validated IDs; entries cannot write workflows or binaries. The privileged submission job checks out only the default branch and reads issue data through the event/API, never shell interpolation. Actions are pinned to a verified upstream commit; no persistent checkout credential is left behind.

Scenarios follow the Android limits of **20 actions and 5 conditions**. `scripts/catalog.py` assigns the compatibility floor and regenerates the exact package byte counts and SHA-256 hashes. The Field Kit tests also verify dependencies, tool references, disabled imports, bounded commands and the separation between automatic reminders and manual executable workflows. CI validates script data; it never executes submitted shell code.

`Offline Mode` is an example that sets local QVars; it does not disable Android radios. Draft scenarios, lab templates and network examples require configuration and deliberate activation. There are no automatic wipe examples. The passphrase sample uses 28 independently selected words from its 24-word demonstration dictionary (about 128 bits before any user changes); do not shorten it while retaining the security claim.
