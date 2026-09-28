# Field Kit validation — 2026-09-28

The 14 tools and 12 scenarios were exercised with Q-P1NG Pro **1.0.174 (app code 175)** on a Pixel running Android 17 and a Samsung running Android 11. Tests use separate app-private preferences, root filesystems and synthetic documents. Personal profiles, contacts and messages are not test inputs.

## Completed checks

| Check | Result |
| --- | --- |
| Repository validation and submission workflow tests | 19 passed |
| Android JVM tests: sandbox, Action Forge, scenarios and automation | 69 passed |
| New device integration cases | 2 passed on each phone |
| Existing automation and process lifecycle regression cases | 32 passed on each phone |
| Android build and Lint | Passed; no new Lint findings |
| Android 16 KiB ELF alignment | 40 native libraries passed the app build gate |

Each new device integration run covers all 26 imports, disabled execution defaults, package availability, all 14 tool commands and all eight manual workflows. It verifies real OCR output, hashes, read-only SQLite queries, PDF diagnostics, shell lint without execution, ZIP inventory without extraction, valid and tampered signatures, YARA matches/non-matches/invalid rules, and the local HTTP laboratory. Missing files, symbolic links, malformed JSON and invalid timestamps fail explicitly. Input file hashes stay unchanged.

The web test starts a temporary loopback fixture on an ephemeral port and changes only the test copy's destination port. The published example remains fixed to `127.0.0.1:8080`. Network-disabled execution is rejected before the script's first line runs. A command without confirmation is rejected and no temporary shell-source file remains.

The four optional reminders are checked for schema, disabled defaults, allowed actions and dependencies. The existing device regression suite covers automation events. This does not claim an overnight 09:00 scheduling or long-duration battery trial for every reminder.

## Corrections discovered during testing

- Inline scripts previously validated only the command that opened a temporary script, omitting the script body from command policy. App code 175 validates the complete source before running it and avoids writing a temporary shell-source file. The app's lexical command checks are not a kernel network firewall or a proof that arbitrary scripts are harmless.
- SQLite uses SQL pragmas for its busy timeout and read-only query mode; this avoids a conflict between its `-cmd` CLI option and the terminal's Android host-command deny rule.
- YARA uses `--timeout=10`. Its short `-t` option selects rule tags and is not a scan timeout. Positive, negative and invalid-rule cases guard against silent false negatives.
- Scenario validation now matches the Android limits of 20 actions and five conditions.

All original 37 package payloads remain byte-for-byte unchanged. New package payloads total 75,491 bytes; the complete index is 32,902 bytes. The app downloads examples separately; they are not bundled in the production APK. Test copies live only in the instrumentation APK. Package line endings are normalized to LF before hashing, matching the committed Git blobs and GitHub downloads.

CI treats submissions as data and never executes shell scripts. A successful schema/hash check does not replace human source review or device tests. For setup and usage, see [the Field Kit guide](FIELD_KIT.md).
