"""Small standard-library helpers, compatible with Debian 9's Python 3.5."""
import hashlib
import json
import os
import posixpath
import re
import shutil
import tarfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATCH_SHA256 = '5fe57ca6ee96d59b36c6e0ca842843c50884f177bef1e85234cf669b577f5e48'


def sha256(path):
    result = hashlib.sha256()
    with open(str(path), 'rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def sources():
    items = json.loads((ROOT / 'sources.lock.json').read_text())['files']
    names = set()
    for item in items:
        name = item['file']
        if not re.match(r'^[A-Za-z0-9_.+~-]+$', name) or name in ('.', '..'):
            raise ValueError('Unsafe source filename')
        if name in names or not re.match(r'^[0-9a-f]{64}$', item['sha256']):
            raise ValueError('Invalid source lock')
        if not item['url'].startswith('https://'):
            raise ValueError('Source URL must use HTTPS')
        names.add(name)
    return items


def verify_cache(cache):
    for item in sources():
        path = cache / item['file']
        if not path.is_file() or sha256(path) != item['sha256']:
            raise ValueError('Missing or mismatched source: ' + item['file'])
    if sha256(cache / 'php74-bailout.patch') != PATCH_SHA256:
        raise ValueError('Upstream patch checksum mismatch')


def fetch(cache):
    cache.mkdir(parents=True, exist_ok=True)
    for item in sources():
        target = cache / item['file']
        if target.exists():
            if sha256(target) != item['sha256']:
                raise ValueError('Refusing to replace mismatched file: ' + str(target))
            print('Verified ' + item['file'])
            continue
        temp = target.with_name(target.name + '.part')
        # Exclusive creation avoids overwriting another download or a pre-existing link.
        with open(str(temp), 'xb') as output:
            with urllib.request.urlopen(item['url'], timeout=90) as response:
                if not response.geturl().startswith('https://'):
                    raise ValueError('Refusing redirect away from HTTPS')
                shutil.copyfileobj(response, output)
        if sha256(temp) != item['sha256']:
            raise ValueError('Downloaded checksum mismatch; inspect ' + str(temp))
        os.rename(str(temp), str(target))
        print('Downloaded and verified ' + item['file'])
    verify_cache(cache)


def unpack(archive, destination):
    """Validate every member before extracting into a fresh, private directory.

    Reject special files, duplicate paths and links escaping the extraction root.
    Also reject descendants of archive symlinks, preventing write-through attacks.
    """
    if destination.exists():
        raise ValueError('Extraction destination must be new')
    with tarfile.open(str(archive)) as stream:
        members = stream.getmembers()
        seen, links = set(), set()
        for member in members:
            name = member.name.rstrip('/')
            if (not name or name.startswith('/') or '\\' in name or ':' in name
                    or '..' in name.split('/') or name != posixpath.normpath(name)):
                raise ValueError('Unsafe archive path: ' + member.name)
            if name in seen:
                raise ValueError('Duplicate archive path: ' + name)
            seen.add(name)
            if not (member.isfile() or member.isdir() or member.issym() or member.islnk()):
                raise ValueError('Special archive member: ' + name)
            if member.issym() or member.islnk():
                target = member.linkname
                if not target or target.startswith('/') or '\\' in target or ':' in target:
                    raise ValueError('Unsafe link target')
                base = posixpath.dirname(name) if member.issym() else ''
                resolved = posixpath.normpath(posixpath.join(base, target))
                if resolved == '..' or resolved.startswith('../'):
                    raise ValueError('Archive link escapes destination')
                links.add(name)
        for name in seen:
            parent = posixpath.dirname(name)
            while parent:
                if parent in links:
                    raise ValueError('Archive writes through a link')
                parent = posixpath.dirname(parent)
        for member in members:
            if member.islnk():
                target = posixpath.normpath(member.linkname)
                if target not in seen or target in links:
                    raise ValueError('Unsupported hardlink target')
        destination.mkdir(parents=True)
        # Validation above is also used on Python versions without extraction filters.
        for member in members:
            member.mode &= 0o777
            member.uid = member.gid = os.getuid() if hasattr(os, 'getuid') else 0
            member.uname = member.gname = ''
        kwargs = {'filter': 'fully_trusted'} if hasattr(tarfile, 'data_filter') else {}
        stream.extractall(str(destination), members=members, **kwargs)
