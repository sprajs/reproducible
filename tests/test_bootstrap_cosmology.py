"""Admission failures must preserve immutable acquisition/build evidence."""
import importlib.util
import io
from pathlib import Path
import tarfile
import tempfile
import subprocess
import unittest
from unittest.mock import patch, Mock

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

    def test_timeout_kills_group_reaps_and_retains_command_log(self):
        for vanished in (False, True):
            with self.subTest(vanished=vanished), tempfile.TemporaryDirectory() as tmp:
                builder = bootstrap.Builder(Path(tmp))
                process = Mock(pid=12345, returncode=-9)
                process.wait.side_effect = [subprocess.TimeoutExpired(['fake'], 1), -9]
                with patch.object(bootstrap.subprocess, 'Popen', return_value=process) as spawn, patch.object(bootstrap.os, 'killpg', side_effect=ProcessLookupError if vanished else None) as kill:
                    with self.assertRaises(subprocess.TimeoutExpired):
                        builder.run(['fake'], timeout=1)
                self.assertTrue(spawn.call_args.kwargs['start_new_session'])
                kill.assert_called_once_with(12345, bootstrap.signal.SIGKILL)
                self.assertEqual(process.wait.call_count, 2)
                self.assertEqual(builder.commands[0]['returncode'], -9)
                self.assertTrue(builder.commands[0]['interrupted'])
                self.assertEqual(builder.commands[0]['log_identity'], bootstrap.pin(Path(tmp) / 'command-000.log'))

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
