import hashlib
import importlib.util
import io
from pathlib import Path
import tarfile
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('restore_preservation', Path(__file__).resolve().parents[1] / 'scripts/restore_preservation.py')
r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)


class RestoreTests(unittest.TestCase):
    def fixture(self, root, corrupt=False):
        data = b'unique unfinished evidence'; sha = hashlib.sha256(data).hexdigest()
        with tarfile.open(root / 'bundle.tar.gz', 'w:gz') as tf:
            info = tarfile.TarInfo('sha256/' + sha)
            body = b'corrupt evidence' if corrupt else data
            info.size = len(body); tf.addfile(info, io.BytesIO(body))
        entries = [{'root_id': 'root00', 'path': 'evidence/failed.txt', 'sha256': sha,
                    'bytes': len(data), 'upload': {'bundle': 'bundle.tar.gz', 'member': 'sha256/' + sha}},
                   {'root_id': 'root01', 'path': '.work/draft.txt', 'sha256': sha,
                    'bytes': len(data), 'upload': {'bundle': 'bundle.tar.gz', 'member': 'sha256/' + sha}}]
        return {'entries': entries, 'objects': [{'kind': 'bundle', 'path': 'bundle.tar.gz'}]}, data

    def test_deduplicated_bytes_recover_to_each_original_root(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td); manifest, data = self.fixture(p); r.recover(p, manifest)
            self.assertEqual((p / 'recovered/root00/evidence/failed.txt').read_bytes(), data)
            self.assertEqual((p / 'recovered/root01/.work/draft.txt').read_bytes(), data)
            with self.assertRaises(FileExistsError):r.recover(p, manifest)

    def test_corrupt_member_refused_before_original_copy(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td); manifest, _ = self.fixture(p, corrupt=True)
            with self.assertRaises(ValueError):r.recover(p, manifest)
            self.assertFalse((p / 'recovered').exists())

    def test_conflicting_deduplicated_identity_refused(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td); manifest, _ = self.fixture(p)
            manifest['entries'][1]['bytes'] += 1
            with self.assertRaises(ValueError):r.recover(p, manifest)
            self.assertFalse((p / 'recovered').exists())

    def test_unsafe_paths_and_null_versions_refused(self):
        for name in ('/absolute', '../escape', 'root/../escape', 'a//b', 'a\\b'):
            with self.assertRaises(ValueError):r.safe(name)
        with tempfile.TemporaryDirectory() as td:
            p = Path(td); manifest, _ = self.fixture(p); manifest['entries'][0]['path'] = '../escape'
            with self.assertRaises(ValueError):r.recover(p, manifest)
            with self.assertRaises(ValueError):r.fetch('s3://research-data-436908790672-eu-west-2/x', 'null', p / 'download', '0' * 64, 1, 'research')

    def test_root_and_wrong_account_refused(self):
        import json
        for account,arn in [('436908790672','arn:aws:iam::436908790672:root'),('000000000000','arn:aws:iam::000000000000:user/research')]:
            response=SimpleNamespace(returncode=0,stdout=json.dumps({'Account':account,'Arn':arn}))
            with patch.object(r.subprocess,'run',return_value=response),self.assertRaises(ValueError):r.check_identity('research')


if __name__ == '__main__':unittest.main()
