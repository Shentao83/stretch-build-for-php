#!/usr/bin/env python3
"""Check and apply the exact upstream patch to the 17 original release files."""
import argparse
import json
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path
from common import ROOT, PATCH_SHA256, sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, default=ROOT / 'downloads')
    parser.add_argument('--git', default='git')
    args = parser.parse_args()
    archive = args.cache / 'php-7.4.33.tar.xz'
    patch = args.cache / 'php74-bailout.patch'
    if sha256(archive) != '924846abf93bc613815c55dd3f5809377813ac62a9ec4eb3778675b82a27b927':
        raise ValueError('PHP source checksum mismatch')
    if sha256(patch) != PATCH_SHA256:
        raise ValueError('Patch checksum mismatch')
    changed = re.findall(r'^diff --git a/(\S+) b/\1$', patch.read_text(), re.M)
    if len(changed) != 17:
        raise ValueError('Unexpected upstream patch shape')
    with tempfile.TemporaryDirectory(prefix='patch-check-') as temp:
        folder = Path(temp)
        with tarfile.open(str(archive)) as stream:
            for relative in changed:
                if relative.startswith('/') or '..' in relative.split('/') or '\\' in relative:
                    raise ValueError('Unsafe patch path')
                member = stream.getmember('php-7.4.33/' + relative)
                if not member.isfile():
                    raise ValueError('Expected regular source file')
                target = folder / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(stream.extractfile(member).read())
        env = os.environ.copy()
        env['GIT_CEILING_DIRECTORIES'] = str(folder.parent)
        env.pop('GIT_DIR', None)
        env.pop('GIT_WORK_TREE', None)
        if shutil.which(args.git):
            base = [args.git, '-c', 'core.autocrlf=false', 'apply', '--whitespace=nowarn']
            commands = [base + ['--check', str(patch.resolve())],
                        base + [str(patch.resolve())]]
            tool = 'git apply'
        else:
            commands = [['patch', '--batch', '--fuzz=0', '-p1', '--dry-run', '-i', str(patch.resolve())],
                        ['patch', '--batch', '--fuzz=0', '-p1', '-i', str(patch.resolve())]]
            tool = 'patch --fuzz=0'
        for command in commands:
            subprocess.check_call(command, cwd=str(folder), env=env)
        print(json.dumps({'status': 'passed', 'changed_files': len(changed),
                          'application_tool': tool,
                          'patch_sha256': PATCH_SHA256,
                          'patched_files': {name: sha256(folder / name) for name in changed}}, indent=2))


if __name__ == '__main__':
    main()
