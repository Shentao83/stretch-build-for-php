# Stretch build recipe for PHP 7.4.33

A community build recipe for an isolated CLI/FPM installation on **Debian 9
(Stretch), amd64**, applying the PHP project's existing bailout mitigation
to the original 7.4.33 release sources.

**Status: experimental source recipe.** This consolidated recipe completed a
fresh build and CLI/FPM smoke tests on Debian 9.13 amd64 on 29 October 2026.
Read [validation and limitations](docs/VALIDATION.md) for the exact scope.
No upstream source/patch contents, binaries, Debian packages or production deployment automation are shipped.

## What this contributes

- A standalone build sequence with private dependency prefixes and no root build.
- A lock file with 16 historical source/package/patch inputs and SHA-256 checksums.
- Automatic download of the unchanged [upstream mitigation](https://github.com/php/php-src/commit/712e60f9edfd03f0960fc4fc3c2c375f42b90aa2),
  credited to Arnaud Le Blanc and Ilija Tovilo.
- A broad compatibility profile with ICU 65.1, libxml2 2.9.9, OpenSSL baseline
  packages and six pinned PECL modules, all documented explicitly.
- CLI and private Unix-socket FPM smoke tests, patch checks and repository checks.

## Security scope

The upstream commit addresses **CVE-2026-109618 and CVE-2026-109619** and describes
itself as a minimal mitigation for an EOL version. We did not author that fix.
This recipe does **not** provide ongoing security support or resolve every
known vulnerability in PHP, Debian or the bundled historical dependencies.

[PHP 7.4 upstream support ended on 28 November 2022](https://www.php.net/eol.php).
[Debian 9 LTS ended in 2022](https://wiki.debian.org/LTS/Stretch);
separate third-party extended support has its own scope. Use this as a
documented bridge while migrating an existing system.

## Getting started

Use a disposable Debian 9 amd64 VM. Fetching on a current workstation and
copying the verified cache into the VM avoids old TLS/client limitations.

```sh
python3 scripts/fetch.py
python3 scripts/fetch.py --verify-only
python3 scripts/check_patch.py
# In the disposable Debian 9 VM, as an unprivileged build user:
python3 scripts/build.py --jobs 2
python3 scripts/smoke.py
```

Install the documented [build prerequisites](docs/BUILD.md) in the disposable
VM first. The build uses only the Python standard library, supports Python
3.5+, and refuses root execution and an existing work directory. Its output
is tied to the absolute build path and is **not relocatable**.

## Documentation

- [Build and prerequisites](docs/BUILD.md)
- [Source and patch provenance](docs/PROVENANCE.md)
- [Validation and known differences](docs/VALIDATION.md)
- [Manual integration and rollback](docs/OPERATIONS.md)
- [German overview](docs/README.de.md)
- [Release notes](CHANGELOG.md) and [contributing](CONTRIBUTING.md)
- [License scope and upstream notices](THIRD_PARTY_NOTICES.md)

This repository is independent of the PHP Group and Debian. No maintenance
schedule or support SLA is promised. Please keep customer data, credentials,
hostnames and production logs out of issues and pull requests.

This product includes PHP software, freely available from
<http://www.php.net/software/>.
