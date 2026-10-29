#!/usr/bin/env python3
"""Build the historical compatibility profile in a disposable Stretch amd64 VM.

No sudo, service changes, global installs, or binary redistribution.
"""
import argparse
import json
import os
import platform
import re
import shlex
import shutil
import signal
import subprocess
import time
from pathlib import Path
from common import ROOT, sha256, unpack, verify_cache


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, default=ROOT / 'downloads')
    parser.add_argument('--work', type=Path, default=ROOT / 'build')
    parser.add_argument('--jobs', type=int, default=2, choices=(1, 2))
    args = parser.parse_args()
    if platform.system() != 'Linux' or os.geteuid() == 0:
        raise SystemExit('Run as an unprivileged user in a disposable Debian 9 amd64 VM.')
    release = Path('/etc/os-release').read_text()
    if not re.search(r'^ID=debian$', release, re.M) or not re.search(r'^VERSION_ID="?9"?$', release, re.M):
        raise SystemExit('This historical recipe requires Debian 9.')
    if platform.machine() != 'x86_64':
        raise SystemExit('Only amd64 is covered by the locked OpenSSL inputs.')
    for tool in ['gcc', 'g++', 'make', 'cmake', 'autoconf', 'pkg-config', 'patch', 'dpkg-deb', 'ldd']:
        if not shutil.which(tool):
            raise SystemExit('Missing build tool: ' + tool + '; see docs/BUILD.md')
    cache = args.cache.resolve()
    # pathlib.resolve() in Python 3.5 requires an existing path.
    work = Path(os.path.realpath(str(args.work)))
    if re.search(r'[^A-Za-z0-9_./-]', str(work)):
        raise SystemExit('Use a work path without spaces or shell metacharacters.')
    verify_cache(cache)
    if work.exists():
        raise SystemExit('Work directory already exists; choose a new --work path.')
    work.mkdir(parents=True)
    private, prefix = work / 'runtime/private', work / 'runtime/php'
    lib = private / 'lib/x86_64-linux-gnu'
    lib.mkdir(parents=True)
    env = {key: value for key, value in os.environ.items()
           if key not in ('LD_PRELOAD', 'LD_LIBRARY_PATH', 'PHP_INI_SCAN_DIR', 'PHPRC',
                          'CFLAGS', 'CXXFLAGS', 'CPPFLAGS', 'LDFLAGS', 'PKG_CONFIG_PATH')}
    env.update({'LC_ALL': 'C', 'CFLAGS': '-O2 -g0', 'CXXFLAGS': '-O2 -g0',
                'CPPFLAGS': '-I' + str(private / 'include'),
                'LDFLAGS': '-L' + str(lib) + ' -Wl,-rpath,' + str(lib),
                'LD_LIBRARY_PATH': str(lib), 'PKG_CONFIG_PATH': str(lib / 'pkgconfig'),
                'PHP_INI_SCAN_DIR': str(prefix / 'etc/php.d')})
    started = time.time()
    packages = subprocess.check_output(['dpkg-query', '-W'])
    (work / 'packages-before.txt').write_bytes(packages)

    def run(argv, cwd, log, timeout=7200):
        argv = [str(x) for x in argv]
        print('Running ' + log + ': ' + argv[0], flush=True)
        with open(str(work / log), 'ab') as output:
            output.write(('RUN ' + repr(argv) + '\n').encode())
            output.flush()
            proc = subprocess.Popen(argv, cwd=str(cwd), env=env, stdout=output,
                                    stderr=output, start_new_session=True)
            try:
                status = proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGTERM)
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait()
                raise
        if status:
            raise RuntimeError('Command failed; inspect ' + str(work / log))

    def source(filename, subdir):
        dest = work / 'source' / filename
        unpack(cache / filename, dest)
        return dest / subdir

    def make_install(folder, log):
        run(['make', '-j' + str(args.jobs)], folder, log)
        run(['make', 'install'], folder, log, 600)

    # Exact historical OpenSSL baseline, extracted privately without maintainer scripts.
    tree = work / 'openssl-packages'
    tree.mkdir()
    lock = json.loads((ROOT / 'sources.lock.json').read_text())
    for item in lock['files']:
        if item['file'].endswith('.deb'):
            path = cache / item['file']
            for key in ('Package', 'Version', 'Architecture'):
                actual = subprocess.check_output(['dpkg-deb', '-f', str(path), key]).decode().strip()
                if actual != item[key.lower()]:
                    raise ValueError('Unexpected Debian package identity')
            run(['dpkg-deb', '-x', path, tree], work, 'openssl.log', 120)
    for name in ('libssl.so.1.1', 'libcrypto.so.1.1', 'libssl.so.1.0.2',
                 'libcrypto.so.1.0.2', 'libssl.so', 'libcrypto.so'):
        src = tree / 'usr/lib/x86_64-linux-gnu' / name
        if src.is_symlink():
            target = os.readlink(str(src))
            if '/' in target:
                raise ValueError('Unexpected OpenSSL symlink')
            (lib / name).symlink_to(target)
        else:
            shutil.copy2(str(src), str(lib / name))
    include = private / 'include/openssl'
    shutil.copytree(str(tree / 'usr/include/openssl'), str(include), symlinks=True)
    conf = include / 'opensslconf.h'
    if conf.is_symlink():
        conf.unlink()
    shutil.copy2(str(tree / 'usr/include/x86_64-linux-gnu/openssl/opensslconf.h'), str(conf))
    (lib / 'pkgconfig').mkdir()
    for name in ('libssl.pc', 'libcrypto.pc', 'openssl.pc'):
        data = (tree / 'usr/lib/x86_64-linux-gnu/pkgconfig' / name).read_text()
        (lib / 'pkgconfig' / name).write_text(data.replace('prefix=/usr', 'prefix=' + str(private)))

    folder = source('icu4c-65_1-src.tgz', 'icu/source')
    run(['./configure', '--prefix=' + str(private), '--libdir=' + str(lib),
         '--disable-static', '--enable-shared', '--disable-tests', '--disable-samples'], folder, 'icu.log')
    make_install(folder, 'icu.log')
    folder = source('libxml2-2.9.9.tar.xz', 'libxml2-2.9.9')
    run(['./configure', '--prefix=' + str(private), '--libdir=' + str(lib),
         '--disable-static', '--enable-shared', '--without-python', '--with-icu'], folder, 'xml.log')
    make_install(folder, 'xml.log')
    folder = source('libzip-1.7.3.tar.xz', 'libzip-1.7.3') / 'build-local'
    folder.mkdir()
    run(['cmake', '..', '-DCMAKE_INSTALL_PREFIX=' + str(private),
         '-DCMAKE_INSTALL_LIBDIR=lib/x86_64-linux-gnu', '-DCMAKE_BUILD_TYPE=Release',
         '-DBUILD_TOOLS=OFF', '-DBUILD_REGRESS=OFF', '-DBUILD_EXAMPLES=OFF', '-DBUILD_DOC=OFF',
         '-DENABLE_GNUTLS=OFF', '-DENABLE_MBEDTLS=OFF'], folder, 'zip.log')
    make_install(folder, 'zip.log')
    folder = source('libsodium-1.0.18.tar.gz', 'libsodium-1.0.18')
    run(['./configure', '--prefix=' + str(private), '--libdir=' + str(lib),
         '--enable-shared', '--disable-static', '--with-pic'], folder, 'sodium.log')
    make_install(folder, 'sodium.log')
    folder = source('argon2-20190702.tar.gz', 'phc-winner-argon2-20190702')
    opts = ['OPTTARGET=none', 'PREFIX=' + str(private), 'LIBRARY_REL=lib/x86_64-linux-gnu',
            'PKGCONFIG_REL=lib/x86_64-linux-gnu', 'ARGON2_VERSION=20190702',
            'CFLAGS=-O2 -g0 -fPIC -std=c89 -Wall -Iinclude -Isrc -pthread']
    run(['make', '-j' + str(args.jobs), 'libs'] + opts, folder, 'argon2.log')
    run(['make', 'install'] + opts, folder, 'argon2.log')

    folder = source('php-7.4.33.tar.xz', 'php-7.4.33')
    patch = cache / 'php74-bailout.patch'
    base = ['patch', '--batch', '--fuzz=0', '-p1', '-i', str(patch)]
    run(base + ['--dry-run'], folder, 'patch.log', 60)
    run(base, folder, 'patch.log', 60)
    options = json.loads((ROOT / 'config/configure-options.json').read_text())
    options = [x.replace('@PREFIX@', str(prefix)).replace('@PRIVATE@', str(private)) for x in options]
    run(['./configure'] + options, folder, 'php-configure.log')
    # The historical configure generates two forced static settings despite --disable-static.
    tool = folder / 'libtool'
    before = tool.read_text()
    if len(re.findall(r'^build_old_libs=yes$', before, re.M)) != 2:
        raise ValueError('Unexpected generated Libtool layout; refusing blind edit')
    tool.write_text(re.sub(r'^build_old_libs=yes$', 'build_old_libs=no', before, flags=re.M))
    make_install(folder, 'php-build.log')
    ext = Path(subprocess.check_output([str(prefix / 'bin/php-config'), '--extension-dir'], env=env).decode().strip())
    if not str(ext.resolve()).startswith(str(prefix.resolve()) + '/'):
        raise ValueError('Extension install path escaped private prefix')
    extras = [
        ('igbinary', '3.2.1', ['--enable-igbinary']),
        ('msgpack', '2.1.2', ['--with-msgpack']),
        ('imagick', '3.4.4', ['--with-imagick=/usr']),
        ('memcache', '4.0.5.2', ['--enable-memcache']),
        ('memcached', '3.1.5', ['--enable-memcached', '--enable-memcached-igbinary',
                             '--enable-memcached-msgpack', '--enable-memcached-json', '--enable-memcached-sasl']),
        ('xdebug', '3.0.3', ['--enable-xdebug'])]
    for name, version, flags in extras:
        folder = source(name + '-' + version + '.tgz', name + '-' + version)
        log = 'pecl-' + name + '.log'
        run([prefix / 'bin/phpize'], folder, log)
        run(['./configure', '--with-php-config=' + str(prefix / 'bin/php-config'), '--with-pic'] + flags, folder, log)
        make_install(folder, log)
        if not (ext / (name + '.so')).is_file():
            raise ValueError('Missing extension: ' + name)

    (prefix / 'etc/php.d').mkdir(parents=True, exist_ok=True)
    ini = (ROOT / 'config/php.ini').read_text().replace('@EXTENSION_DIR@', str(ext))
    (prefix / 'etc/php.ini').write_text(ini)
    for name, binary in [('run-php', 'bin/php'), ('run-fpm', 'sbin/php-fpm')]:
        text = ('#!/bin/sh\nset -eu\nunset LD_PRELOAD PHPRC\n'
                'export LD_LIBRARY_PATH={lib}\nexport PHP_INI_SCAN_DIR={scan}\n'
                'exec {binary} -c {ini} "$@"\n').format(
                    lib=shlex.quote(str(lib)), scan=shlex.quote(str(prefix / 'etc/php.d')),
                    binary=shlex.quote(str(prefix / binary)), ini=shlex.quote(str(prefix / 'etc/php.ini')))
        (work / name).write_text(text)
        (work / name).chmod(0o755)
    run([work / 'run-php', ROOT / 'tests/smoke.php'], work, 'cli-smoke.log', 60)
    run([work / 'run-fpm', '-v'], work, 'fpm-version.log', 60)
    for binary in [prefix / 'bin/php', prefix / 'sbin/php-fpm'] + list(ext.glob('*.so')):
        result = subprocess.check_output(['ldd', str(binary)], env=env).decode()
        if 'not found' in result:
            raise ValueError('Unresolved shared library: ' + str(binary))
    if packages != subprocess.check_output(['dpkg-query', '-W']):
        raise ValueError('Global package inventory changed during build')
    report = {'status': 'built-cli-smoke-passed', 'patch_sha256': sha256(patch),
              'source_sha256': sha256(cache / 'php-7.4.33.tar.xz'),
              'configure_options': options, 'jobs': args.jobs,
              'elapsed_seconds': round(time.time() - started, 1),
              'global_packages_unchanged': True,
              'php_sha256': sha256(prefix / 'bin/php'),
              'fpm_sha256': sha256(prefix / 'sbin/php-fpm'),
              'limitation': 'Non-relocatable local build; run scripts/smoke.py for FPM; no full CVE coverage claim'}
    (work / 'build-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Build complete. Run: python3 scripts/smoke.py --work ' + str(work))


if __name__ == '__main__':
    main()
