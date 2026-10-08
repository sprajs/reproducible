"""Challenge cloud byte verification and refusal paths without AWS credentials."""
import contextlib
import copy
import io
import json
import shutil
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import cloud_storage as cs


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'a').mkdir()
        (self.source / 'a' / 'value').write_bytes(b'research\0bytes')
        (self.source / 'a.txt').write_text('table')
        self.rows = cs.inventory(self.source)
        self.store = cs.Storage('reproducible')

    def manifest(self):
        return {'schema': 'research-snapshot-v1', 'snapshot': 'attempt',
                'namespace': 'reproducible', 'files': copy.deepcopy(self.rows)}

    def test_manifest_order_matches_inventory_and_corruption_changes_hash(self):
        self.assertEqual(cs.validate_manifest(self.manifest()), self.rows)
        (self.source / 'a.txt').write_text('other')
        self.assertNotEqual(cs.inventory(self.source), self.rows)

    def test_unsafe_and_colliding_paths_refused(self):
        for name in ('../escape', '/tmp/escape', 'a//b', 'a/./b', 'a\\b', 'a\nb'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                cs.safe_path(name)
        doc = self.manifest()
        doc['files'].append(dict(doc['files'][0]))
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            cs.validate_manifest(doc)
        doc = self.manifest()
        doc['files'].append({'path': 'a', 'bytes': 0, 'sha256': 'a' * 64})
        with self.assertRaisesRegex(ValueError, 'Conflicting'):
            cs.validate_manifest(doc)

    def test_symlink_refused_including_directory(self):
        (self.source / 'linked').symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'Symlinks'):
            cs.inventory(self.source)

    def test_remote_verification_requires_all_and_only_correct_bytes(self):
        valid = ''.join(f'{r["sha256"]}  {r["path"]}\n' for r in self.rows)
        with patch.object(self.store, 'rclone', return_value=valid) as call:
            self.store.verify_remote('remote', self.rows)
            self.assertIn('--download', call.call_args.args)
        for bad in ('', valid.replace(self.rows[0]['sha256'], '0' * 64),
                    valid + '0' * 64 + '  unexpected\n', valid + valid):
            with self.subTest(bad=bad), patch.object(self.store, 'rclone', return_value=bad), self.assertRaises(ValueError):
                self.store.verify_remote('remote', self.rows)

    def test_failed_upload_never_writes_manifest(self):
        with patch.object(self.store, 'rclone', return_value='') as call, \
             patch.object(self.store, 'verify_remote', side_effect=ValueError('bad bytes')), \
             contextlib.redirect_stdout(io.StringIO()), self.assertRaises(ValueError):
            self.store.push(self.source, 'failed')
        self.assertFalse(any('copyto' == c.args[0] for c in call.call_args_list))

    def test_changed_source_never_writes_manifest(self):
        with patch.object(self.store, 'rclone', return_value='') as call, \
             patch.object(self.store, 'verify_remote'), \
             patch.object(cs, 'inventory', side_effect=[self.rows, []]), \
             contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(ValueError, 'Source changed'):
            self.store.push(self.source, 'changed')
        self.assertFalse(any('copyto' == c.args[0] for c in call.call_args_list))

    def test_restore_refuses_existing_destination_before_transfer(self):
        with patch.object(self.store, 'rclone') as call, self.assertRaisesRegex(ValueError, 'must not exist'):
            self.store.pull('attempt', self.source, 'a' * 64)
        call.assert_not_called()

    def test_wrong_manifest_hash_does_not_create_destination(self):
        def transfer(*args):
            Path(args[2]).write_text(json.dumps(self.manifest()))
            return ''
        destination = self.root / 'restore'
        with patch.object(self.store, 'rclone', side_effect=transfer) as call, self.assertRaisesRegex(ValueError, 'Manifest SHA-256'):
            self.store.pull('attempt', destination, 'a' * 64)
        self.assertEqual(call.call_count, 1)
        self.assertFalse(destination.exists())

    def test_root_and_wrong_account_refused(self):
        for account, arn in [('436908790672', 'arn:aws:iam::436908790672:root'),
                             ('000000000000', 'arn:aws:iam::000000000000:user/someone')]:
            with patch.object(self.store, 'aws', return_value={'Account':account,'Arn':arn}), self.assertRaises(ValueError):
                self.store.check_identity()

    def test_restore_checks_downloaded_bytes_and_retains_corruption(self):
        manifest = self.root / 'manifest.json'
        manifest.write_text(json.dumps(self.manifest()))
        for corrupt in (False, True):
            destination = self.root / str(corrupt)
            def transfer(*args):
                if args[0] == 'copyto':
                    shutil.copyfile(manifest, args[2])
                else:
                    shutil.copytree(self.source, args[2], dirs_exist_ok=True)
                    if corrupt:
                        (Path(args[2]) / 'a.txt').write_text('corrupted')
                return ''
            with patch.object(self.store, 'rclone', side_effect=transfer), contextlib.redirect_stdout(io.StringIO()):
                if corrupt:
                    with self.assertRaisesRegex(ValueError, 'Restored bytes failed'):
                        self.store.pull('attempt', destination, cs.digest(manifest))
                    self.assertEqual((destination / 'a.txt').read_text(), 'corrupted')
                else:
                    self.store.pull('attempt', destination, cs.digest(manifest))
                    self.assertEqual(cs.inventory(destination), self.rows)


if __name__ == '__main__':
    unittest.main()
