"""Adversarial new-route support, calibration and failed-prefix controls."""
import importlib.util
import math
from pathlib import Path
import types
import unittest
import io
import json
import sys
import tempfile
from unittest import mock

PATH = Path(__file__).resolve().parents[1] / "experiments/planck-primary-reference/adapter.py"
SPEC = importlib.util.spec_from_file_location("primary_reference_adapter", PATH)
adapter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(adapter)
CONTROLLER_SPEC = importlib.util.spec_from_file_location("primary_reference_controller", PATH.with_name("controller.py"))
controller = importlib.util.module_from_spec(CONTROLLER_SPEC)
with mock.patch.dict(sys.modules, {"adapter": adapter}):
    CONTROLLER_SPEC.loader.exec_module(controller)
adapter = controller.adapter


class PrimaryReferenceTest(unittest.TestCase):
    def test_numerical_failure_never_becomes_negative_infinity(self):
        contract = {"bounds": {name: [0, 100] for name in adapter.COORDINATES},
                    "calibration_prior": {"mean": 1, "sigma": .0025},
                    "production_policy": "base", "limits": {"max_evaluations": 10, "evaluation_wall_seconds": 10}}
        class RefusingTheory:
            def evaluate(self, *_args, **_kwargs):
                raise adapter.NumericalRefusal("native refusal", {"phase": "CLASS"})
        journal = io.StringIO()
        journal.fileno = lambda: 123
        with mock.patch.dict(sys.modules, {"scipy.stats": types.SimpleNamespace(
                truncnorm=lambda *_args, **_kwargs: None, uniform=lambda **_kwargs: None)}), \
                mock.patch.object(controller.os, "fsync"):
            evaluator = controller.Evaluator(contract, RefusingTheory(), None, journal,
                                             controller.time.monotonic()+10)
            with self.assertRaises(adapter.NumericalRefusal):
                evaluator.logtarget([.022, .12, 67, 3, .96, .05, 1])
        events = [json.loads(line) for line in journal.getvalue().splitlines()]
        self.assertEqual([row["status"] for row in events], ["started", "numerical_refused"])
        self.assertNotIn("logtarget", events[-1])

    def test_exception_statuses_remain_distinct(self):
        for exc, status in [(KeyboardInterrupt(), "user_interrupted"),
                            (controller.ResourceInterrupted(), "resource_interrupted"),
                            (ValueError(), "software_refused"),
                            (adapter.LikelihoodUnsupported("x", {}), "likelihood_unsupported")]:
            self.assertEqual(controller.refusal_status(exc), status)

    def test_resource_interrupt_survives_actual_adapter_path(self):
        class InterruptedClass:
            def set(self, _):
                pass
            def compute(self):
                raise controller.ResourceInterrupted("actual CLASS call deadline")
            def struct_cleanup(self):
                pass
            def empty(self):
                pass
        contract = {"bounds": {name: [0, 100] for name in adapter.COORDINATES},
                    "class_fixed": {"YHe": "BBN", "sBBN file": "/explicit/pinned/table"},
                    "production_policy": "base", "numerical_policies": {"base": {}}}
        theory = adapter.ClassOwner(types.SimpleNamespace(Class=InterruptedClass), contract)
        with self.assertRaises(controller.ResourceInterrupted) as caught:
            theory.evaluate([.022, .12, 67, 3, .96, .05, 1])
        self.assertEqual(controller.refusal_status(caught.exception), "resource_interrupted")

    def test_native_hung_child_is_killed_reaped_and_recorded(self):
        # A native pause never returns to Python to deliver a Python handler.
        script = "import ctypes; ctypes.CDLL(None).pause()"
        with tempfile.TemporaryDirectory() as root:
            attempt = Path(root) / "attempt"
            result = controller.supervise([sys.executable, "-c", script], attempt,
                                          {"attempt_wall_seconds": .3, "evaluation_wall_seconds": .2})
            self.assertEqual(result["status"], "resource_interrupted")
            self.assertLess(result["worker_returncode"], 0)
            saved = json.loads((attempt / "terminal.json").read_bytes())
            self.assertEqual(saved, result)

    def test_stdout_overflow_stops_with_exact_bounded_prefix(self):
        script = "import os; os.write(1,b'x'*65536); import ctypes; ctypes.CDLL(None).pause()"
        with tempfile.TemporaryDirectory() as root:
            attempt = Path(root) / "attempt"
            result = controller.supervise([sys.executable, "-c", script], attempt,
                                          {"attempt_wall_seconds": 5, "evaluation_wall_seconds": 5,
                                           "logs_bytes": 1024, "attempt_bytes": 1048576,
                                           "file_bytes": 131072})
            self.assertEqual(result["status"], "resource_interrupted")
            self.assertEqual(result["resource_limit"], "logs_bytes")
            self.assertEqual((attempt / "worker.stdout.log").read_bytes(), b"x"*1024)

    def test_input_bound_refuses_before_json_parse(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "input.json"
            path.write_bytes(b"{}" + b" "*controller.CONFIG_BYTES)
            with self.assertRaisesRegex(ValueError, "byte bound"):
                controller.read_json(path)

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
