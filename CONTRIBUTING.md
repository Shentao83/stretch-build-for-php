# Contributing

Keep changes small and include the reason, affected dependency versions and
validation performed. Preserve upstream attribution and license notices.

Run `python3 scripts/verify_repository.py`,
`python3 -m unittest discover -s tests -v`, and the source/patch checks.
For build changes, publish sanitized results from a fresh disposable Debian 9
amd64 VM, including package/toolchain versions and CLI/FPM smoke results.
State explicitly when a check was not run.

The upload manifest is an integrity record, not a secret-scanning guarantee.
After reviewing intentional changes, regenerate its hashes with
`python3 scripts/update_manifest.py`, then rerun verification.

Do not submit customer configuration, hostnames, IP inventories, credentials,
production reports, VM images, downloaded dependency archives or binaries.
Discuss dependency/version changes before treating them as compatible with
the historical profile. Contributions do not imply a maintenance commitment.
