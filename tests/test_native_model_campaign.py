"""Challenge the dedicated controller's admission and qualification boundaries."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

FOLDER = Path(__file__).resolve().parents[1] / 'experiments/native-model-campaign'
spec = importlib.util.spec_from_file_location('native_campaign', FOLDER / 'controller.py')
controller = importlib.util.module_from_spec(spec)
spec.loader.exec_module(controller)


class NativeCampaignAdmission(unittest.TestCase):
    def test_duplicate_and_nonfinite_json_refused(self):
        for raw in ('{"x":1,"x":2}', '{"x":NaN}'):
            with self.assertRaises(ValueError):
                controller.strict_json(raw)

    def test_linked_input_and_dirty_source_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'input').write_text('data')
            (root / 'link').symlink_to(root / 'input')
            with self.assertRaises(ValueError):
                controller.pin(root / 'link')

    def test_missing_refinement_partner_and_coverage_refused(self):
        request = json.loads((FOLDER / 'request.json').read_text())
        report = {'schema': 'compiled-native-model-campaign/v1', 'profile': 'quick',
                  'build_id': request['sdk_pin']['build_id'],
                  'request_sha256': controller.pin(FOLDER / 'request.json')['sha256'],
                  'observations': None, 'inference': None, 'controls': [{'passed': True}], 'cases': []}
        # Each selected family represented; one-sided comparisons are not qualified.
        for family in request['models']:
            report['cases'].append({'family': family, 'id': family, 'resolution': 'default',
                                    'model_id': family, 'parameters': {}, 'rows': []})
        request['expected_cases'] = len(report['cases']); request['expected_rows']['quick'] = 0
        with self.assertRaisesRegex(ValueError, 'partner'):
            controller.qualification(report, request, 'quick')
        for case in list(report['cases']):
            other = copy.deepcopy(case); other['resolution'] = 'refined'; report['cases'].append(other)
        report['cases'][0]['rows'].append({'coordinate': 1, 'values': {}})
        request['expected_cases'] = len(report['cases']); request['expected_rows']['quick'] = 1
        with self.assertRaisesRegex(ValueError, 'coverage'):
            controller.qualification(report, request, 'quick')
