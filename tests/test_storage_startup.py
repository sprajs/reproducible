import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

SPEC = importlib.util.spec_from_file_location('storage_startup', Path(__file__).resolve().parents[1] / 'scripts/storage_startup.py')
startup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(startup)


class StartupTests(unittest.TestCase):
    def test_catalog_failure_retains_access_evidence_and_is_not_ready(self):
        with tempfile.TemporaryDirectory() as td, patch.object(startup, 'run_check', side_effect=[
            {'status': 'passed', 'result': {'identity': 'restricted'}},
            {'status': 'failed', 'reason': 'missing catalog'},
        ]):
            receipt, path = startup.startup(Path(td) / 'new', ['--ambient-credentials'])
            self.assertFalse(receipt['ready'])
            self.assertEqual(json.loads(path.read_text()), receipt)
            self.assertEqual(receipt['checks']['access']['result']['identity'], 'restricted')

    def test_access_failure_does_not_fetch_catalog(self):
        with tempfile.TemporaryDirectory() as td, patch.object(startup, 'run_check', return_value={'status': 'failed'}) as check:
            receipt, _ = startup.startup(Path(td) / 'new', ['--profile', 'research'])
            self.assertFalse(receipt['ready'])
            check.assert_called_once_with('status', ['--profile', 'research'])
            self.assertEqual(receipt['checks']['catalog']['status'], 'not_attempted')

    def test_discovery_preserves_catalog_pin_and_never_overwrites_receipt(self):
        catalog = {'catalog_pin': {'uri': 's3://bucket/catalog', 'sha256': 'a' * 64, 'version_id': 'exact'}, 'entries': []}
        with tempfile.TemporaryDirectory() as td, patch.object(startup, 'run_check', side_effect=[
            {'status': 'passed', 'result': {}}, {'status': 'passed', 'result': catalog},
        ]):
            destination = Path(td) / 'new'
            receipt, path = startup.startup(destination, [])
            self.assertTrue(receipt['ready'])
            self.assertEqual(receipt['checks']['catalog']['result'], catalog)
            original = path.read_bytes()
            with self.assertRaises(FileExistsError):
                startup.startup(destination, [])
            self.assertEqual(path.read_bytes(), original)

    def test_subprocess_failure_does_not_record_output(self):
        process = Mock(returncode=1)
        process.communicate.return_value = ('sensitive-output', 'sensitive-error')
        with patch.object(startup.subprocess, 'Popen', return_value=process) as launch:
            check = startup.run_check('status', ['--ambient-credentials'])
            self.assertEqual(check['status'], 'failed')
            self.assertNotIn('sensitive', json.dumps(check))
            process.communicate.assert_called_once_with(timeout=90)
            self.assertNotIn('shell', launch.call_args.kwargs)

    @unittest.skipUnless(startup.os.name == 'posix', 'POSIX process-group cleanup')
    def test_timeout_kills_aws_child_group(self):
        process = Mock(pid=123)
        process.communicate.side_effect = [subprocess.TimeoutExpired('aws', 90), ('', '')]
        with patch.object(startup.subprocess, 'Popen', return_value=process), patch.object(startup.os, 'killpg') as kill:
            self.assertEqual(startup.run_check('catalog', [])['status'], 'failed')
            kill.assert_called_once_with(123, startup.signal.SIGKILL)
            self.assertEqual(process.communicate.call_count, 2)

    def test_invalid_json_is_a_failure(self):
        process = Mock(returncode=0)
        process.communicate.return_value = ('bad-json', '')
        with patch.object(startup.subprocess, 'Popen', return_value=process):
            self.assertEqual(startup.run_check('catalog', [])['status'], 'failed')
