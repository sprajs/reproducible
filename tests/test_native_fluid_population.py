"""Adversarial admission fixtures, not scientific model calculations."""
import importlib.util
import json
from pathlib import Path
import unittest

FOLDER = Path(__file__).resolve().parents[1] / 'experiments/native-fluid-population'
spec = importlib.util.spec_from_file_location('fluid_population', FOLDER / 'controller.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


class FluidPopulationAdmission(unittest.TestCase):
    def fixture(self):
        r = json.loads((FOLDER / 'request.json').read_text())
        r['sdk_pin'] = {'build_id': 'test-only'}
        r['parameters']['chaplygin'].update(a_s=[0], alpha=[0])
        r['parameters']['plummer_population'].update(M_kg=[1], b_m=[1])
        r['coordinates']['quick'] = {'a': [1], 'radius_over_scale': [0], 'speed_over_native_escape': [1]}
        r.update(expected_cases=4, expected_rows={'quick': 4}, expected_radius_states={'quick': 2})
        cases = []
        for (family, i), pars in c.expected_states(r).items():
            for resolution in ('default', 'refined'):
                values = {k: {'status': 0, 'value': 1} for k in c.CG_METRICS}
                case = {'family': family, 'id': i, 'parameters': pars, 'model_id': r['model_ids'][family], 'resolution': resolution, 'rows': [{'coordinate': 1, 'values': values}]}
                if family == 'plummer_population':
                    case['radius_states'] = [{'coordinate': 0, 'values': {k: {'status': 0, 'value': 1} for k in c.RADIUS_METRICS}}]
                    case['rows'] = [{'coordinate': {'radius_index': 0, 'radius_over_scale': 0, 'speed_over_native_escape': 1}, 'support': 3, 'native_status': 8, 'binding_energy_m2_s2': 0, 'binding_energy_absolute_error_m2_s2': 1, 'values': {k: {'status': 8, 'value': None} for k in c.VELOCITY_METRICS}}]
                cases.append(case)
        ids = ['compiled-FLRW-endpoint-' + str(i) for i in range(8)] + ['GCG-future-outside-domain-withheld', 'negative-speed-refused', 'native-outside-support-diagnostic-zero']
        return r, {'schema': 'compiled-native-fluid-population/v1', 'profile': 'quick', 'build_id': 'test-only', 'request_sha256': 'test', 'observations': None, 'inference': None, 'cases': cases, 'controls': [{'id': x, 'passed': True} for x in ids]}

    def test_boundary_cannot_hide_inconsistent_support(self):
        r, report = self.fixture()
        self.assertFalse(c.qualify(report, r, 'quick', 'test')['failures'])
        report['cases'][2]['rows'][0]['support'] = 1
        self.assertTrue(c.qualify(report, r, 'quick', 'test')['failures'])

    def test_complete_axis_binding(self):
        r, report = self.fixture()
        report['cases'][0]['rows'][0]['coordinate'] = .5
        with self.assertRaises(ValueError):
            c.qualify(report, r, 'quick', 'test')

    def test_nonfinite_overflow_and_duplicate_literals(self):
        for raw in ('{"x":1e999}', '{"x":NaN}', '{"x":1,"x":2}'):
            with self.assertRaises(ValueError):
                c.strict_json(raw)

    def test_cli_exit_is_integer_and_distinguishes_gates(self):
        self.assertEqual(c.exit_code({'status': 'completed', 'numerical': {'failures': []}}), 0)
        self.assertEqual(c.exit_code({'status': 'completed', 'numerical': {'failures': [{}]}}), 1)
        self.assertEqual(c.exit_code({'status': 'failed'}), 1)
