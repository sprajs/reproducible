import hashlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import acquire_dataset_inputs as acquisition


class AcquisitionFailureTests(unittest.TestCase):
    def asset(self, raw=b'good'):
        return {'expected_bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
                'acquisition_routes': [{'kind': 'pinned_download', 'urls': ['https://example.invalid/original']}]}

    def test_valid_exact_transfer_cap_admits_without_extra_probe(self):
        with tempfile.TemporaryDirectory() as td, patch.object(acquisition.urllib.request, 'urlopen', return_value=io.BytesIO(b'good')):
            target = Path(td) / 'original'
            result = acquisition.acquire(self.asset(), target, 8, 4)
            self.assertEqual(result['status'], 'acquired_exact_upstream')
            self.assertEqual(target.read_bytes(), b'good')
            self.assertEqual(result['received_bytes'], 4)
            self.assertFalse(result['upstream_eof_checked'])

    def test_changed_bytes_are_preserved_without_admission(self):
        with tempfile.TemporaryDirectory() as td, patch.object(acquisition.urllib.request, 'urlopen', return_value=io.BytesIO(b'evil')):
            target = Path(td) / 'original'
            result = acquisition.acquire(self.asset(), target, 8, 8)
            self.assertEqual(result['status'], 'failed')
            self.assertFalse(target.exists())
            self.assertEqual((Path(td) / 'original.attempt-0.partial').read_bytes(), b'evil')
            self.assertEqual(result['received_bytes'], 4)

    def test_transfer_cap_charges_retained_partial(self):
        with tempfile.TemporaryDirectory() as td, patch.object(acquisition.urllib.request, 'urlopen', return_value=io.BytesIO(b'changed and too long')):
            result = acquisition.acquire(self.asset(), Path(td) / 'original', 8, 3)
            self.assertEqual(result['status'], 'failed')
            self.assertEqual(result['received_bytes'], 3)
            self.assertEqual(result['attempts'][0]['partial_bytes'], 3)

    def test_oversize_response_preserved_and_no_final_output(self):
        with tempfile.TemporaryDirectory() as td, patch.object(acquisition.urllib.request, 'urlopen', return_value=io.BytesIO(b'good!')):
            target = Path(td) / 'original'
            result = acquisition.acquire(self.asset(), target, 8, 8)
            self.assertFalse(target.exists())
            self.assertEqual(result['attempts'][0]['partial_bytes'], 5)

    def test_interruption_records_partial_hash(self):
        class Interrupted(io.BytesIO):
            def read(self, size=-1):
                if self.tell():
                    raise KeyboardInterrupt()
                return super().read(2)
        with tempfile.TemporaryDirectory() as td, patch.object(acquisition.urllib.request, 'urlopen', return_value=Interrupted(b'good')):
            result = acquisition.acquire(self.asset(), Path(td) / 'original', 8, 8)
            self.assertEqual(result['status'], 'interrupted')
            self.assertEqual(result['received_bytes'], 2)
            self.assertEqual(result['attempts'][0]['partial_sha256'], hashlib.sha256(b'go').hexdigest())

    def test_invalid_length_refused_without_network(self):
        with tempfile.TemporaryDirectory() as td, patch.object(acquisition.urllib.request, 'urlopen') as network:
            asset = self.asset()
            asset['expected_bytes'] = '4'
            self.assertEqual(acquisition.acquire(asset, Path(td) / 'original', 8, 8)['status'], 'blocked')
            network.assert_not_called()
