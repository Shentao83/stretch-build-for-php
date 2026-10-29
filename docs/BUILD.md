# Build in a disposable Debian 9 amd64 VM

The work directory contains the complete non-relocatable runtime. Choose its
absolute path before building. Keep at least 6 GiB disk free; 2 compiler jobs
and 4 GiB RAM are a practical starting point. Resource needs vary.

## VM prerequisites

Configure your disposable VM's APT sources to the appropriate authenticated
Debian archive or your maintained mirror. Check dates/signatures using the
archive's guidance. This repository does not disable APT signature checks or
replace your sources automatically.

Install these packages **inside the disposable VM only**:

```sh
sudo apt-get update
sudo apt-get install --no-install-recommends \
  python3 ca-certificates xz-utils patch build-essential pkg-config autoconf \
  bison re2c cmake git libtool libxml2-dev libcurl4-openssl-dev libssl-dev \
  libicu-dev libzip-dev libonig-dev libldap2-dev libpng-dev libjpeg62-turbo-dev \
  libfreetype6-dev libwebp-dev libxpm-dev libxslt1-dev zlib1g-dev libbz2-dev \
  libedit-dev libffi-dev libsodium-dev libmagickwand-dev libmemcached-dev \
  libsasl2-dev libevent-dev
```

The package list specifies prerequisites, not a fully locked VM image. APT
package revisions and dynamic host resources remain outside the source lock.
Record `dpkg-query -W` with any published build results.

## Inputs

On a current workstation, from the repository root:

```sh
python3 scripts/fetch.py
python3 scripts/fetch.py --verify-only
python3 scripts/check_patch.py
```

Copy the repository and `downloads/` directory into the VM without changing
the source bytes. Files in downloads are ignored by Git. To use an alternate
cache, pass `--cache /absolute/path` to fetch, check_patch and build.

## Build and smoke tests

As an unprivileged user, from the repository root:

```sh
python3 scripts/verify_repository.py
python3 -m unittest discover -s tests -v
python3 scripts/build.py --work "$HOME/stretch-build" --jobs 2
python3 scripts/smoke.py --work "$HOME/stretch-build"
"$HOME/stretch-build/run-php" -v
"$HOME/stretch-build/run-php" -m
```

Use a path containing only letters, digits, underscores, slashes, dots and
hyphens. The build refuses a pre-existing work directory, including a partial
build; diagnose its logs and choose a fresh path for another run.

## Sequence and output

1. Verify all locked inputs and the unchanged patch before invoking build tools.
2. Extract the three historical OpenSSL .deb files to a private tree; copy
   headers and libraries without installing packages or executing maintainer scripts.
3. Build private ICU, libxml2, libzip, libsodium and Argon2.
4. Apply the upstream patch to PHP 7.4.33 with zero fuzz, configure the profile
   in `config/configure-options.json`, compile with `-O2 -g0`, and install privately.
5. Adjust the two generated Libtool `build_old_libs` settings to use PIC
   objects, as in the original build. Refuse an unexpected generated layout.
6. Build all six PECL modules against the newly built runtime. Xdebug is
   compiled but disabled in the default INI.
7. Write dedicated CLI/FPM launchers, check shared-library resolution and run
   CLI smoke tests. A separate command exercises an isolated FPM master.

`build-report.json`, `smoke-report.json`, package inventory and per-stage logs
remain in the work directory. CLI/FPM launchers set private library and INI
paths. No alternatives, service units, web handlers or global linker paths
are changed by the build. A failed build does not undo its private directory.

## Redistribution

This initial release is source-only. Do not upload the build directory as a
binary release without a separate dependency/license/source-offer review and
qualification on the intended target. The runtime still uses system libraries
and host resources. Copying its directory elsewhere will not preserve paths.
