"""Controller controls are synthetic, not evidence for the observational fit."""
import importlib.util
import datetime
import io
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "experiments/observational-cosmology"


def module(name):
    spec = importlib.util.spec_from_file_location("observational_" + name, FOLDER / (name + ".py"))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


controller = module("controller")
acquire = module("acquire")
plot = module("plot")


class ObservationalCosmologyTests(unittest.TestCase):
    def test_conditional_search_recovers_known_interior_minimum(self):
        result = controller.fit_profile(lambda h: 3.0 + ((h - 67.12) / 2) ** 2, "quick")
        self.assertLess(abs(result["best_evaluated"]["H0"] - 67.12), .05)
        self.assertLessEqual(result["search_width_km_s_Mpc"], .05)
        self.assertIsNone(result["uncertainty_interval"])

    def test_search_refuses_boundary_and_nonfinite(self):
        for objective in (lambda h: h, lambda h: float("nan")):
            with self.assertRaises(ValueError):
                controller.fit_profile(objective, "quick")

    def test_selection_preserves_off_diagonal_covariance(self):
        data = {"rows": [0, 1, 2], "covariance": [[4, 1, .5], [1, 9, 2], [.5, 2, 16]]}
        result = controller.select_data(data, [0, 2])
        self.assertEqual(result["covariance"], [[4, .5], [.5, 16]])
        for invalid in ([2, 0], [0, 0], [3], [True], []):
            with self.assertRaises(ValueError):
                controller.select_data(data, invalid)

    def test_explicit_alternative_closure(self):
        p = controller.parameters("constant-w", 68.0, full=True)
        self.assertNotIn("Omega_fld", p)
        self.assertEqual(p["Omega_Lambda"], "0")
        self.assertEqual((p["w0_fld"], p["wa_fld"], p["cs2_fld"], p["use_ppf"]),
                         ("-0.9", "0", "1", "yes"))
        self.assertEqual(p["m_ncdm"], "0.06")
        self.assertEqual(controller.parameters("lcdm", 68)["omega_b"], p["omega_b"])
        self.assertNotIn("non linear", controller.parameters("lcdm", 68))

    def test_actual_new_input_renderer_admits_changed_h0_and_output_policy(self):
        for model in controller.MODELS:
            for full in (False, True):
                raw = controller.render_input(model, 61.25, "/tmp/class-output", full=full)
                rows = dict(line.split(" = ", 1) for line in raw.decode().splitlines())
                self.assertEqual(rows.pop("root"), "/tmp/class-output")
                self.assertEqual(rows, controller.parameters(model, 61.25, full=full))
        with self.assertRaises(ValueError):
            controller.render_input("lcdm", 68, "/tmp/bad\noutput")

    def test_unconsumed_fluid_controls_refuse(self):
        physical = controller.parameters("constant-w", 68)
        self.assertEqual(controller.parameter_consumption(b"modes = s\n", physical, full=False)["status"], "passed")
        for raw, full in ((b"w0_fld = -0.9\n", False), (b"modes = s\n", True),
                          (b"modes = t\n", False)):
            with self.assertRaises(ValueError):
                controller.parameter_consumption(raw, physical, full=full)

    def test_official_product_tree_refuses_undeclared_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            declared = []
            for _, relative in controller.score_admission.PRODUCTS:
                product = root / relative
                product.mkdir(parents=True)
                member = product / "declared"
                member.write_bytes(b"original")
                declared.append(controller.pin(member))
            config = {"plc_root": str(root), "admission_files": declared}
            self.assertEqual(len(controller.planck_product_tree(config, time.monotonic() + 10)["files"]), 3)
            (product / "unexpected").write_bytes(b"extra")
            with self.assertRaises(ValueError):
                controller.planck_product_tree(config, time.monotonic() + 10)

    def test_changed_existing_input_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / acquire.bao.INPUTS[0]["relative_path"]
            target.parent.mkdir(parents=True)
            target.write_bytes(b"changed")
            with self.assertRaises(ValueError):
                acquire.acquire(directory, opener=lambda *a, **kw: self.fail("unexpected download"))
            self.assertEqual(target.read_bytes(), b"changed")

    def test_bad_download_never_publishes_target(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                acquire.acquire(directory, opener=lambda *a, **kw: io.BytesIO(b"bad"))
            self.assertFalse((Path(directory) / acquire.bao.INPUTS[0]["relative_path"]).exists())

    def test_separate_input_root_is_used_before_and_after_attempt(self):
        # Synthetic route fixture; no CLASS run or observational score.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inputs = root / "restored"
            inputs.mkdir()
            runtime = root / "runtime.json"
            runtime.write_text("{}")
            data = {"source_identities": [{"sha256": "fixture"}]}
            deadline = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=2)).isoformat()
            with mock.patch.object(controller, "source_state", return_value={}), \
                    mock.patch.object(controller, "verify_runtime", return_value={}), \
                    mock.patch.object(controller.bao, "read_data", return_value=data) as reader, \
                    mock.patch.object(controller, "select_data", side_effect=ValueError("fixture stops before physics")):
                result = controller.execute(runtime, root / "attempt", "quick", deadline, input_root=inputs)
            self.assertEqual(reader.call_args_list, [mock.call(str(inputs)), mock.call(str(inputs))])
            self.assertEqual(result["input_root"], str(inputs))
            self.assertEqual(result["data_before"], result["data_after"])
            self.assertEqual(result["status"], "failed")
            self.assertIn("fixture stops before physics", result["errors"][0]["message"])

    def test_separate_input_root_changed_exact_release_bytes_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inputs = root / "restored"
            originals = {}
            for item in controller.bao.INPUTS:
                target = inputs / item["relative_path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                originals[target] = b"x" * item["bytes"]
                target.write_bytes(originals[target])
            runtime = root / "runtime.json"
            runtime.write_text("{}")
            deadline = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=2)).isoformat()
            with mock.patch.object(controller, "source_state", return_value={}), \
                    mock.patch.object(controller, "verify_runtime", return_value={}):
                result = controller.execute(runtime, root / "attempt", "quick", deadline, input_root=inputs)
            self.assertEqual(result["status"], "failed")
            self.assertIn("consumed input hash identity differs", result["errors"][0]["message"])
            self.assertNotIn("data_before", result)
            for target, original in originals.items():
                self.assertEqual(target.read_bytes(), original)

    def test_input_root_admission_refuses_links_and_traversal_before_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inputs = root / "restored"
            inputs.mkdir()
            linked = root / "linked"
            linked.symlink_to(inputs, target_is_directory=True)
            deadline = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=2)).isoformat()
            for index, invalid in enumerate((linked, inputs / ".." / "restored", root / "missing")):
                with mock.patch.object(controller.transport, "load_json") as loader:
                    result = controller.execute(root / "runtime.json", root / f"attempt-{index}",
                                                "quick", deadline, input_root=invalid)
                loader.assert_not_called()
                self.assertEqual(result["status"], "failed")
                self.assertTrue((root / f"attempt-{index}" / "manifest.json").is_file())

    def test_missing_runtime_attempt_retains_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            runtime = path / "runtime.json"
            runtime.write_text("{}")
            # Source admission will refuse the live edited tree; either refusal
            # still requires a complete retained terminal record.
            deadline = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=2)).isoformat()
            result = controller.execute(runtime, path / "attempt", "quick", deadline)
            self.assertEqual(result["status"], "failed")
            self.assertTrue((path / "attempt/manifest.json").is_file())

    def test_failed_inventory_still_retains_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            deadline = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=2)).isoformat()
            with mock.patch.object(controller.transport, "seal_inventory", side_effect=ValueError("inventory refused")):
                result = controller.execute(path / "absent.json", path / "nested/attempt", "quick", deadline)
            self.assertEqual(result["inventory"]["status"], "refused")
            self.assertEqual(json.loads((path / "nested/attempt/manifest.json").read_text())["status"], "failed")

    def test_plot_product_admission_uses_restored_relative_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = root / "original.json"
            original.write_text('{"restored": true}')
            identity = controller.pin(original)
            restored = root / "restored"
            restored.mkdir()
            original.rename(restored / "product.json")
            self.assertEqual(plot.admitted(identity, restored, "product.json"), {"restored": True})
            with self.assertRaises(ValueError):
                plot.admitted(identity, restored, "../product.json")


if __name__ == "__main__":
    unittest.main()
