# Field Kit for Q-P1NG

14 local tools and 12 workflows, designed for reporters, researchers and operators who need repeatable checks on their own files. English is the default language of these downloadable examples. No private credentials or real case data are included.

## Start in the app

1. Use **Pro 1.0.174 or newer**. Open the Community marketplace in Q-Scenario or Action Forge, then **Refresh catalog via Tor**. Search for a tool by name or choose its category. Downloads and catalog refresh use the app's existing Tor-only client.
2. Download the tool first and inspect its full JSON. Importing leaves it **OFF**. Install the named Linux Sandbox packages separately in **Tool Packs**; those package downloads use the route shown there (currently direct HTTPS to Alpine).
3. Create `fieldkit` in the private sandbox workspace. The tools see it as `/workspace/fieldkit`. Copy your chosen input files there with the exact names below. Tools reject missing, empty, oversized or symbolic-link inputs. They do not search all your files or read chat text as shell code.
4. Review and enable the imported tool in Action Forge. Enable the sandbox and use **Ask every time** for these reviewed commands. Press Review / Run when ready. A tool does not grant itself network, execution or lab permissions.
5. To use the matching Q-Scenario workflow, import it separately. Tool dependencies are stated in its description; they are not silently downloaded or activated. Executable workflows run manually. Reminders can be enabled individually after review.

You do not need to enable all 12 scenarios. Keep the ones useful to your workflow; the others remain disabled and idle. No new perpetual worker is part of a tool. Scheduled reminders use the existing Android scheduling behaviour and can be deferred by the system.

## Tools and inputs

All filenames in this table are under `/workspace/fieldkit`. The package IDs are the exact names in Tool Packs. Original files are not rewritten. File content shown in a local result may be sensitive: sharing the result remains an explicit app action.

| Tool | Packages | Inputs | Result |
| --- | --- | --- | --- |
| File Fingerprint | `file`, `b3sum` | `input.bin` | Type, SHA-256 and BLAKE3; up to 32 MiB |
| File Metadata Report | `exiftool` | `input.bin` | Metadata JSON, including any location tags; up to 32 MiB |
| PDF Structure Check | `qpdf` | `input.pdf` | Syntax diagnostics and page count; up to 32 MiB |
| Offline English OCR | `tesseract-ocr`, `tesseract-ocr-data-eng` | `input.png` | English text; one thread, 60 seconds, input up to 8 MiB |
| Shell Script Review | `shellcheck`, `shfmt` | `input.sh` | POSIX shell lint and formatting diff without running the script; up to 128 KiB |
| JSON Structure Summary | `jq` | `input.json` | One document's type, length and up to 40 keys; values omitted, up to 2 MiB |
| SQLite Read-Only Check | `sqlite` | `input.db` | Quick integrity check and up to 40 table/view names, without row values; up to 32 MiB |
| Compare Two Text Files | `diffutils` | `before.txt`, `after.txt` | Unified diff; each file up to 1 MiB |
| ZIP Inventory Without Extraction | `unzip` | `input.zip` | Central-directory listing only, up to 32 MiB |
| Verify a Minisign Signature | `minisign` | `input.bin`, `signer.pub`, `input.minisig` | Detached-signature verification; evidence up to 32 MiB |
| Zstandard Integrity Check | `zstd` | `input.zst` | Format check without writing decompressed data; input up to 32 MiB, decoder window 64 MiB |
| Local YARA Rule Match | `yara` | `rules.yar`, `input.bin` | Matches from your reviewed rules; rules 64 KiB, input 8 MiB, scan timeout 10 seconds |
| Incident Timeline Summary | `jq` | `events.json` | Event count, UTC range and source counts; up to 2,000 events / 2 MiB, event text omitted |
| Loopback Web Lab | `ffuf` | `words.txt` and your local server | Bounded path checks on `127.0.0.1:8080` only |

Hashes establish byte equality, not source authenticity. Metadata inspection does not remove metadata. PDF/ZIP structure checks are not malware checks; a YARA match is an indicator, not a diagnosis. A Minisign public key must be trusted independently of the file it accompanies. Use a consistent exported SQLite database; copying only a live database while omitting its WAL can lose recent transactions.

For OCR, use a reasonably sized page image: compressed file size does not bound the decoded pixel count. Verify names and numbers against the original. English data is included in the requirement; another language needs its own installed Tesseract data and an explicitly edited command.

### Timeline example

Save this fictional data as `events.json`. Timestamps use strict UTC `YYYY-MM-DDTHH:MM:SSZ`; invalid dates and multiple concatenated JSON documents are rejected.

```json
[
  {"timestamp":"2026-09-28T09:00:00Z","source":"desk","text":"Fictional observation"},
  {"timestamp":"2026-09-28T09:15:00Z","source":"desk","text":"Fictional follow-up"}
]
```

### Loopback laboratory

This is the only new tool that declares network use. It never starts a server, downloads a wordlist or changes settings. Prepare your own HTTP fixture on **the same phone**, with `health` and `missing` in `words.txt`, one per line. Only 1–20 alphanumeric names (plus `_` and `-`) are accepted. Redirect following is not enabled.

After inspecting the complete command, explicitly enable the existing Security Lab and **Open** sandbox network setting for the test. The current lexical allowlist cannot enforce dynamically generated ffuf targets, so the app rejects ffuf in Allowlist mode. The shipped command fixes the destination to loopback; the manifest's host list is review metadata, not an additional operating-system firewall. This example does not send a user's file or chat content as a request body.

The command uses one worker, two requests per second, a two-second request timeout and a 20-second total limit. Stop your own server afterwards and turn off the lab/network setting when no longer needed. No privileged packet capture, radio injection or root capability is implied.

## Event → condition → action

Every scenario imports disabled. Automatic scenarios contain only generic notifications and, where indicated, one local pending flag. They do not include file contents in notifications, change radio states, stop active transfers, transmit data, or execute a tool in the background. Notification permission and OS scheduling restrictions still apply.

| Scenario | Event | Condition | Action / prerequisite |
| --- | --- | --- | --- |
| Fingerprint a File | Manual | Files and tool available | Run File Fingerprint |
| Review a PDF | Manual | Files and tool available | Run PDF Structure Check |
| OCR with Battery Check | Manual | Battery at least 20% | Run Offline English OCR |
| Review a Shell Script | Manual | Files and tool available | Run Shell Script Review |
| Check Local Data | Manual | Both inputs and tools available | JSON summary, then SQLite check; stop on error |
| Verify Received Evidence | Manual | Independently trusted signer key | Run Verify a Minisign Signature |
| Local Web Lab | Manual | Explicit lab/network grant and own server | Run Loopback Web Lab |
| Queue a Review Reminder | Manual | None | Set `%Q_FIELDKIT_REVIEW_PENDING=true`; no report contents |
| Review When Charging | Charging starts | Pending flag is `true` | Generic notification, then clear the flag |
| Low Battery Reminder | Battery crosses 20% downward | Battery at most 20% | Generic reminder; active work is untouched |
| Offline Work Reminder | Wi-Fi disconnects | None | Generic local-work reminder; routing is unchanged |
| Daily Review Reminder | 09:00 device time | Enabled by the user | Generic checklist reminder; timing may be deferred |

Run each imported tool independently first so missing packages/files and policy settings can be corrected before running a multi-step workflow. Q-Scenario's final result is the last action's report; Check Local Data therefore ends with the database report. Detailed report output is not automatically copied into QVars, Vault notes or chat by these examples.

## Maintainer notes

- The catalogue contains executable command **text**, not Linux binaries. Packages are installed separately through the app. Each upstream program retains its own license; the repository's MIT license covers these authored examples.
- `fieldkit.*` and `qscenario.fieldkit.*` entries require app code 175 because inline shell source must be checked by the sandbox policy before execution. Existing entries keep their original compatibility floor.
- `fieldkit-requirements.json` documents prerequisites for automated cross-checks; it is not executed or fetched automatically by the Android marketplace.
- Catalogue CI checks schema, hashes, dependencies, graph references, disabled defaults and finite execution metadata. It never executes submitted scripts. Device validation uses the app's actual parsers, isolated rootfs/preferences and fictional data.
- Primary command references: [jq manual](https://jqlang.org/manual/), [qpdf CLI](https://qpdf.readthedocs.io/en/stable/cli.html), [Tesseract CLI](https://tesseract-ocr.github.io/tessdoc/Command-Line-Usage.html), [Minisign](https://github.com/jedisct1/minisign), [YARA CLI](https://yara.readthedocs.io/en/stable/commandline.html), [ffuf](https://github.com/ffuf/ffuf), and the packages' local help pages.
