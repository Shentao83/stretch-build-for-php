#!/usr/bin/env python3
"""Refresh public-file hashes after reviewing intentional repository edits."""
import json
from common import ROOT, sha256

files = {}
for path in sorted(ROOT.rglob('*')):
    parts = path.relative_to(ROOT).parts
    relative = path.relative_to(ROOT).as_posix()
    if (parts[0] in ('.git', 'downloads', 'build') or parts[0].startswith('build-')
            or '__pycache__' in parts or relative == 'UPLOAD-MANIFEST.json'):
        continue
    if path.is_symlink():
        raise ValueError('Unexpected symlink: ' + relative)
    if path.is_file():
        files[relative] = {'sha256': sha256(path), 'bytes': path.stat().st_size}
(ROOT / 'UPLOAD-MANIFEST.json').write_text(json.dumps({
    'format': 1, 'scope': 'Reviewed source-only upload; downloads and build outputs excluded',
    'files': files}, indent=2) + '\n')
print('Recorded ' + str(len(files)) + ' public files')
