"""Tests for fail-closed source verification and extraction boundaries."""
import io
import json
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from common import ROOT, PATCH_SHA256, sha256, sources, unpack, verify_cache


class HelpersTest(unittest.TestCase):
    def test_lock_and_patch(self):
        locked = sources()
        self.assertEqual(next(x['sha256'] for x in locked if x['file'] == 'php74-bailout.patch'), PATCH_SHA256)
        self.assertEqual(len(locked), 16)

    def test_missing_cache_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                verify_cache(Path(folder))

    def archive(self, entries, folder):
        path = Path(folder) / 'input.tar'
        with tarfile.open(str(path), 'w') as output:
            for name, kind, link in entries:
                info = tarfile.TarInfo(name)
                info.type = kind
                info.linkname = link
                output.addfile(info, io.BytesIO(b''))
        return path

    def test_regular_file_and_internal_symlink(self):
        with tempfile.TemporaryDirectory() as folder:
            archive = self.archive([('src/file', tarfile.REGTYPE, ''),
                                    ('src/link', tarfile.SYMTYPE, 'file')], folder)
            if sys.platform == 'win32':
                # Symlink creation requires a Windows privilege; validation itself is tested below.
                archive = self.archive([('src/file', tarfile.REGTYPE, '')], folder)
            unpack(archive, Path(folder) / 'out')
            self.assertTrue((Path(folder) / 'out/src/file').is_file())

    def test_unsafe_archives_rejected_before_extraction(self):
        attacks = [
            [('../outside', tarfile.REGTYPE, '')],
            [('/absolute', tarfile.REGTYPE, '')],
            [('C:/outside', tarfile.REGTYPE, '')],
            [('src/link', tarfile.SYMTYPE, '../../outside')],
            [('src/link', tarfile.SYMTYPE, 'target'), ('src/link/file', tarfile.REGTYPE, '')],
            [('src/device', tarfile.CHRTYPE, '')],
            [('src/file', tarfile.REGTYPE, ''), ('src/file', tarfile.REGTYPE, '')],
            [('src/link', tarfile.LNKTYPE, '../outside')]]
        for entries in attacks:
            with tempfile.TemporaryDirectory() as folder:
                archive = self.archive(entries, folder)
                target = Path(folder) / 'out'
                with self.assertRaises(ValueError):
                    unpack(archive, target)
                self.assertFalse(target.exists())


if __name__ == '__main__':
    unittest.main()
