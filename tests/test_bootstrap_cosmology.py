"""Admission failures must preserve immutable acquisition/build evidence."""
import importlib.util
import io
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1] / 'scripts/bootstrap_cosmology.py'
spec = importlib.util.spec_from_file_location('bootstrap_cosmology', MODULE)
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)


class BootstrapAdmission(unittest.TestCase):
    def test_hash_mismatch_retains_original_download(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / 'archive'
            with patch.object(bootstrap.urllib.request, 'urlopen', return_value=io.BytesIO(b'wrong source')):
                with self.assertRaisesRegex(ValueError, 'SHA256'):
                    bootstrap.download(dest, ('https://example.test/source', '0' * 64, 1024))
            self.assertEqual(dest.read_bytes(), b'wrong source')
            with patch.object(bootstrap.urllib.request, 'urlopen', return_value=io.BytesIO(b'new')):
                with self.assertRaises(FileExistsError):
                    bootstrap.download(dest, ('https://example.test/source', '0' * 64, 1024))
            self.assertEqual(dest.read_bytes(), b'wrong source')

    def test_archive_refuses_traversal_and_links_before_writes(self):
        for name, kind in [('../outside', tarfile.REGTYPE), ('source/link', tarfile.SYMTYPE), ('source/hard', tarfile.LNKTYPE)]:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                archive = Path(tmp) / 'source.tar'
                with tarfile.open(archive, 'w') as stream:
                    info = tarfile.TarInfo('source/safe'); info.size = 2
                    stream.addfile(info, io.BytesIO(b'ok'))
                    info = tarfile.TarInfo(name); info.type = kind; info.linkname = '/outside'
                    stream.addfile(info)
                output = Path(tmp) / 'extract'
                with self.assertRaises(ValueError):
                    bootstrap.extract(archive, output)
                self.assertFalse(output.exists())

    def test_selected_extraction_keeps_exact_only_required_products(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / 'source.tar'
            with tarfile.open(archive, 'w') as stream:
                for name, raw in [('data/keep/a', b'observed'), ('data/other/b', b'unselected')]:
                    info = tarfile.TarInfo(name); info.size = len(raw)
                    stream.addfile(info, io.BytesIO(raw))
            output = Path(tmp) / 'extract'
            bootstrap.extract(archive, output, ['data/keep'])
            self.assertEqual((output / 'data/keep/a').read_bytes(), b'observed')
            self.assertFalse((output / 'data/other').exists())

    def test_existing_or_external_runtime_root_refused_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / 'source'; marker.write_text('preserve')
            with self.assertRaises(ValueError):
                bootstrap.bootstrap(Path(tmp), True)
            with self.assertRaises(ValueError):
                bootstrap.bootstrap(Path(tmp) / 'fresh', True)
            self.assertEqual(marker.read_text(), 'preserve')
            self.assertFalse((Path(tmp) / 'fresh').exists())


if __name__ == '__main__':
    unittest.main()
