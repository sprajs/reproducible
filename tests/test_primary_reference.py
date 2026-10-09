"""Adversarial new-route support, calibration and failed-prefix controls."""
import importlib.util
import math
from pathlib import Path
import types
import unittest

PATH = Path(__file__).resolve().parents[1] / "experiments/planck-primary-reference/adapter.py"
SPEC = importlib.util.spec_from_file_location("primary_reference_adapter", PATH)
adapter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(adapter)


class PrimaryReferenceTest(unittest.TestCase):
    def test_calibration_guard_precedes_table_index(self):
        support = {"unit": 1, "stepEE_native_float32": 0.0001, "nstepsEE": 3000}
        # This point is within the uncalibrated table but exceeds it after
        # the official map calibration; a fixed-A guard would wrongly pass.
        ee = [0.0, 0.0] + [0.1 * 2*math.pi/(ell*(ell+1)) for ell in range(2, 30)]
        self.assertEqual(adapter.guard_simall({"EE": ee}, 1.0, support)["status"], "passed")
        with self.assertRaises(adapter.LikelihoodUnsupported) as caught:
            adapter.guard_simall({"EE": ee}, 0.5, support)
        self.assertEqual(caught.exception.record["ell"], 2)
        self.assertGreater(caught.exception.record["ratio"], 3000)

    def test_solver_and_cleanup_failures_both_survive(self):
        class BrokenClass:
            def set(self, _):
                pass
            def compute(self):
                raise ValueError("original solver refusal")
            def struct_cleanup(self):
                raise ValueError("cleanup refused")
            def empty(self):
                self.emptied = True
        contract = {"bounds": {name: [0, 100] for name in adapter.COORDINATES},
                    "class_fixed": {"YHe": "BBN", "sBBN file": "/explicit/pinned/table"},
                    "production_policy": "base", "numerical_policies": {"base": {}}}
        owner = adapter.ClassOwner(types.SimpleNamespace(Class=BrokenClass), contract)
        with self.assertRaises(adapter.NumericalRefusal) as caught:
            owner.evaluate([.022, .12, 67, 3, .96, .05, 1])
        self.assertEqual(caught.exception.record["error"], "original solver refusal")
        self.assertEqual(caught.exception.record["cleanup"]["failures"][0]["operation"], "struct_cleanup")
        self.assertTrue(owner.owner.emptied)

    def test_no_fixed_helium_or_fixed_varied_coordinate(self):
        contract = {"bounds": {name: [0, 100] for name in adapter.COORDINATES},
                    "class_fixed": {"YHe": "0.2454", "sBBN file": "/explicit/pinned/table"},
                    "production_policy": "base", "numerical_policies": {"base": {}}}
        values = [.022, .12, 67, 3, .96, .05, 1]
        with self.assertRaisesRegex(ValueError, "BBN-consistent"):
            adapter.class_parameters(values, contract)
        contract["class_fixed"]["YHe"] = "BBN"
        contract["class_fixed"]["omega_b"] = .022
        with self.assertRaisesRegex(ValueError, "varied cosmological"):
            adapter.class_parameters(values, contract)


if __name__ == "__main__":
    unittest.main()
