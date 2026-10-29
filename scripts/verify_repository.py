#!/usr/bin/env python3
"""Verify the upload allowlist, checksums, source lock and public-file boundaries."""
import ast
import json
import re
from pathlib import Path
from common import ROOT, sha256, sources


def main():
    sources()
    expected = json.loads((ROOT / 'UPLOAD-MANIFEST.json').read_text())['files']
    actual = set()
    excluded_roots = ('.git', 'downloads', 'build')
    for path in ROOT.rglob('*'):
        relative = path.relative_to(ROOT).as_posix()
        parts = path.relative_to(ROOT).parts
        if parts[0] in excluded_roots or parts[0].startswith('build-') or '__pycache__' in parts:
            continue
        if path.is_symlink():
            raise ValueError('Unexpected repository symlink: ' + relative)
        if not path.is_file() or relative == 'UPLOAD-MANIFEST.json':
            continue
        actual.add(relative)
        if relative not in expected or sha256(path) != expected[relative]['sha256']:
            raise ValueError('Unexpected or modified file: ' + relative)
        if path.stat().st_size > 2 * 1024 * 1024:
            raise ValueError('Unexpected large file: ' + relative)
        content = path.read_text(encoding='utf-8')
        forbidden = [r'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----',
                     r'gh[pousr]_[A-Za-z0-9]{20,}', r'github_pat_[A-Za-z0-9_]{20,}',
                     r'AKIA[0-9A-Z]{16}', r'(?i)C:[\\/]Users[\\/]',
                     r'\b10\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
                     r'\b192\.168\.\d{1,3}\.\d{1,3}\b',
                     r'[A-Za-z0-9.!#$%&\x27*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+',
                     r'(?i)(?:password|passwd|api[_-]?key|client[_-]?secret|access[_-]?token)\s*[:=]\s*[\x22\x27][^\x22\x27\s]{6,}[\x22\x27]']
        for pattern in forbidden:
            # The scanner's own patterns are descriptions, not actual credentials.
            if relative != 'scripts/verify_repository.py' and re.search(pattern, content):
                raise ValueError('Private-looking content: ' + relative)
        if path.suffix == '.py':
            ast.parse(content, filename=relative)
    if actual != set(expected):
        raise ValueError('Missing files: ' + repr(sorted(set(expected) - actual)))
    print(json.dumps({'status': 'passed', 'verified_files': len(actual),
                      'scope': 'Allowlist, hashes, source-lock shape, Python syntax and basic credential patterns'}))


if __name__ == '__main__':
    main()
