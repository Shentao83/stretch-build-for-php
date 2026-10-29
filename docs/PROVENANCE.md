# Source and patch provenance

## PHP source and mitigation

- Release: [PHP 7.4.33](https://www.php.net/releases/7_4_33.php).
- Source: <https://www.php.net/distributions/php-7.4.33.tar.xz>.
- Release hash reference: <https://www.php.net/releases/index.php?json&version=7.4.33>.
- Source SHA-256: `924846abf93bc613815c55dd3f5809377813ac62a9ec4eb3778675b82a27b927`.
- Upstream commit: [712e60f9edfd03f0960fc4fc3c2c375f42b90aa2](https://github.com/php/php-src/commit/712e60f9edfd03f0960fc4fc3c2c375f42b90aa2).
- Patch URL: <https://github.com/php/php-src/commit/712e60f9edfd03f0960fc4fc3c2c375f42b90aa2.patch>.
- Patch SHA-256: `5fe57ca6ee96d59b36c6e0ca842843c50884f177bef1e85234cf669b577f5e48`.
- Authors: Arnaud Le Blanc; co-author Ilija Tovilo. Original patch headers retained.
- Advisories: [GHSA-w8hw-w9fx-j79w](https://github.com/php/php-src/security/advisories/GHSA-w8hw-w9fx-j79w)
  and [GHSA-6wmf-4rv5-p3rp](https://github.com/php/php-src/security/advisories/GHSA-6wmf-4rv5-p3rp).

The patch is downloaded unchanged into the ignored local cache. The contribution here is the independent
build recipe and documentation, not authorship of the upstream vulnerability fix.
`scripts/check_patch.py` checks and applies all 17 modified files against the
verified original release. It does not compile or execute that source.

## Dependency lock

`sources.lock.json` records URLs and SHA-256 values from the original local
build inputs. It pins PHP, ICU 65.1, libxml2 2.9.9, libzip 1.7.3, libsodium
1.0.18, Argon2 20190702, six PECL archives, three archived Debian OpenSSL
packages, and the unchanged upstream patch. No upstream patch, source archive, downloaded package or executable is vendored.

The OpenSSL packages are libssl1.1 and libssl-dev `1.1.0l-1~deb9u3`, plus
libssl1.0.2 `1.0.2u-1~deb9u4`, all amd64. The older ABI is retained for system
dependencies, not selected as a modern security baseline.

PHP's source checksum was compared with official release metadata. The
original libxml checksum was checked against the upstream SHA-256 listing;
ICU's official MD5 matched and its SHA-256 was recorded. The original Debian
Snapshot content hashes and historical Packages/Release metadata were checked
locally; a valid archive signature was recorded alongside expired-key status.
Those original machine-specific evidence files are not published here.

The public scripts enforce the recorded SHA-256 values. They do not repeat
GPG verification or claim that every source has a verified detached signature.
Archive identity and transport verification do not imply current security support.

The VM's APT package revisions, compiler/toolchain, build paths, timestamps,
and host resources are not fully pinned. This is a recipe with pinned primary
inputs, not a claim of bit-for-bit reproducibility.
