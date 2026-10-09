import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
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

    def test_named_transport_recovers_originals_with_classification_pin(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td); manifest,data=self.fixture(p)
            classification=json.dumps(manifest).encode(); classification_sha=hashlib.sha256(classification).hexdigest()
            name='shared/archives/test'; release='a'*64; prefix='s3://research-data-436908790672-eu-west-2/'+name+'/versions/'+release
            payloads={'manifest.json':classification,'bundle.tar.gz':(p/'bundle.tar.gz').read_bytes()}
            rows=[{'path':name,'uri':prefix+'/files/'+name,'version_id':'v1','bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()} for name,body in payloads.items()]
            doc={'schema':'research-named-manifest/v1','collection':name,'release':release,'files':rows,'provenance':{'classification_manifest_sha256':classification_sha}}
            marker=json.dumps(doc).encode(); marker_uri=prefix+'/manifest.json'; bodies={row['uri']:payloads[row['path']] for row in rows};bodies[marker_uri]=marker
            def fetch(uri,version,dest,sha,size,profile):
                body=bodies[uri]
                self.assertEqual(hashlib.sha256(body).hexdigest(),sha);dest.write_bytes(body)
            storage_path=Path(__file__).resolve().parents[1]/'scripts/research_storage.py'
            storage_spec=importlib.util.spec_from_file_location('research_storage',storage_path)
            storage_module=importlib.util.module_from_spec(storage_spec);storage_spec.loader.exec_module(storage_module)
            class FakeStorage:
                def __init__(self,*args):pass
                def get(self,pin,path):fetch(pin['uri'],pin['version_id'],path,pin['sha256'],pin.get('bytes'),None)
                def key(self,uri):return uri.removeprefix('s3://research-data-436908790672-eu-west-2/')
            storage_module.Storage=FakeStorage
            destination=p/'restored'; argv=['restore','--manifest-uri',marker_uri,'--manifest-sha256',hashlib.sha256(marker).hexdigest(),'--manifest-version-id','v1','--destination',str(destination),'--recover-roots']
            with patch.dict(sys.modules,{'research_storage':storage_module}),patch.object(sys,'argv',argv),patch.object(r,'check_identity'),patch.object(r,'fetch',side_effect=fetch),patch('sys.stdout',new=io.StringIO()):r.main()
            self.assertEqual((destination/'recovered/root00/evidence/failed.txt').read_bytes(),data)
            self.assertEqual((destination/'recovered/root01/.work/draft.txt').read_bytes(),data)


if __name__ == '__main__':unittest.main()
