# Validation and known differences

## Historical candidate, 27 October 2026

The original private candidate passed a local qualification covering 52
functional groups and 32 requests. Its final report recorded no compiler
errors, 16 compiler warnings, unchanged global VM packages, unchanged runtime
files after tests, and successful installation/removal checks.

`reports/historical-validation.json` contains only selected aggregate fields.
It is a maintainer-supplied historical summary; private logs and environments
are not included, so it is not independently reproducible evidence by itself.

## Public consolidated recipe

The public scripts consolidate the former staged build, replace deployment
paths and rebuild PECL modules instead of copying earlier module binaries.
The original qualification does not automatically qualify this new recipe.

On 29 October 2026, the consolidated recipe completed a fresh build in a new
work directory in an existing disposable Debian 9.13 amd64 VM, using Python
3.5.3 and GCC 6.3.0. All six PECL modules were rebuilt. CLI smoke tests and
private Unix-socket FPM smoke tests passed, including checks for 43 required
extensions plus OPcache. Global package inventory remained unchanged.

The build took approximately 529 seconds with two compiler jobs in this test
environment. This is an observation, not a build-time guarantee.
`reports/preparation-validation.json` records selected sanitized results and
the source, patch, binary and package-inventory hashes. It contains no raw
host configuration or deployment logs.

The complete upstream test suite, exploit regression tests, application
qualification, pristine-VM bootstrap and binary redistribution qualification
have not been run for this public recipe.

The GitHub workflow checks file integrity, helpers, downloads and patch
application. A green workflow does not indicate a complete Stretch build.

## Compatibility and security limits

- The original target used external PCRE2 10.36. The recipe uses PHP 7.4.33's
  bundled PCRE2 10.35. Synthetic regex success cannot establish application parity.
- ICU 65.1 and libxml2 2.9.9 match the historical upstream version numbers;
  parity with all downstream vendor patches is not established.
- Historical OpenSSL and other dependency versions reproduce a compatibility
  baseline and may contain unrelated vulnerabilities.
- Compiler warning count is a historical observation, not a clean-build claim.
- System libraries, ImageMagick coders/delegates/policies, fonts, NSS, locale
  data, timezone data and the CA store remain host resources.
- FPM smoke tests use a private socket and synthetic PHP only. No database,
  mail, HTTP API, authentication flow or customer business workflow is tested.
- The CVE patch does not change `PHP_VERSION`; version banners alone cannot
  prove patch presence. Keep source hashes, patch logs and build reports.
- No exploit-based regression test or comprehensive CVE audit is included.
- Older PHP installations and the operating system require separate treatment.
- The local build is non-relocatable and is not a `.deb` package.

Before operational use, qualify the exact fresh build and its application
workflows in staging, verify backups/restores, and retain a tested rollback.
Migration to maintained OS and PHP versions remains necessary.
