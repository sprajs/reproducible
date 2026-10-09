"""Admit an exact production SDK, execute bounded native responses, retain evidence."""
import argparse
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
FOLDER = Path(__file__).resolve().parent
ENV = {key: "1" for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "BLIS_NUM_THREADS")}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def clean_path(path):
    path = Path(path).absolute()
    require(".." not in path.parts and not any(p.is_symlink() for p in (path, *path.parents)), "linked/traversing path refused")
    return path


def pin(path, limit=268435456):
    path = clean_path(path)
    require(path.is_file() and path.stat().st_size <= limit, "bounded regular file required")
    before = path.stat()
    raw = path.read_bytes()
    after = path.stat()
    require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns), "file drift during consumed read")
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def strict_json(raw):
    def pairs(items):
        out = {}
        for key, value in items:
            require(key not in out, "duplicate JSON key")
            out[key] = value
        return out
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")))


def write(path, value):
    with Path(path).open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def source_state(root):
    root = clean_path(root)
    revision = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    dirty = subprocess.check_output(["git", "-C", str(root), "status", "--porcelain"], text=True)
    require(not dirty, "clean committed source required")
    return {"revision": revision, "dirty": False}


def sdk_state(sdk, engine, manifest_path, request):
    sdk, engine = clean_path(sdk), clean_path(engine)
    manifest_pin = pin(manifest_path, 4194304)
    require(manifest_pin["sha256"] == request["sdk_pin"]["build_manifest_sha256"], "qualified build manifest hash differs")
    manifest = strict_json(Path(manifest_pin["path"]).read_text())
    require(manifest["git_head"] == request["engine_revision"] and not manifest["git_status"] and
            manifest["profile"] == "release" and manifest["build_id"] == request["sdk_pin"]["build_id"], "qualified production build identity differs")
    require(source_state(engine)["revision"] == request["engine_revision"], "engine source revision differs")
    rows = []
    require(0 < len(manifest["sources"]) <= 2048, "source inventory bound")
    for relative, expected in manifest["sources"].items():
        require(not Path(relative).is_absolute() and ".." not in Path(relative).parts, "source manifest path refused")
        item = pin(engine / relative, 16777216)
        require(item["sha256"] == expected, "engine source hash differs")
    for path in sorted(sdk.rglob("*")):
        require(not path.is_symlink(), "linked SDK member refused")
        if path.is_file():
            require(len(rows) < 1024, "SDK inventory bound")
            rows.append({**pin(path), "relative_path": str(path.relative_to(sdk))})
    require(rows and sum(row["bytes"] for row in rows) <= 268435456, "SDK total byte bound")
    library = pin(sdk / "lib/libirred_core.a")
    require(library["sha256"] == request["sdk_pin"]["library_sha256"], "qualified installed library hash differs")
    for name in ("quintessence", "dgp_growth", "nfw_halo", "decaying_matter", "curved_flrw", "hernquist_sphere"):
        require(pin(sdk / "include/irred" / (name + ".hpp"))["sha256"] ==
                manifest["sources"]["cpp/include/irred/" + name + ".hpp"], "installed model header source differs")
    return {"manifest": manifest_pin, "build_id": manifest["build_id"], "library": library, "files": rows}


def qualification(report, request, profile):
    require(report["schema"] == "compiled-native-model-campaign/v1" and report["profile"] == profile and
            report["build_id"] == request["sdk_pin"]["build_id"] and
            report["request_sha256"] == pin(FOLDER / "request.json")["sha256"], "native response identity differs")
    require(report["observations"] is None and report["inference"] is None, "synthetic role changed")
    require(len(report["cases"]) == request["expected_cases"] and
            sum(len(case["rows"]) for case in report["cases"]) == request["expected_rows"][profile], "native sweep row count differs")
    require({case["family"] for case in report["cases"]} == set(request["models"]), "native model family selection differs")
    grouped = {}
    for case in report["cases"]:
        key = (case["family"], case["id"])
        require(case["resolution"] not in grouped.setdefault(key, {}), "duplicate native case resolution")
        grouped[key][case["resolution"]] = case
    comparisons, failures = [], []
    gate = request["numerical_gate"]
    for key, pair in grouped.items():
        require(set(pair) == {"default", "refined"}, "missing numerical comparison partner")
        a, b = pair["default"], pair["refined"]
        require(a["parameters"] == b["parameters"] and a["model_id"] == b["model_id"], "comparison physical state changed")
        require(len(a["rows"]) == len(b["rows"]), "comparison row coverage differs")
        for i, (first, second) in enumerate(zip(a["rows"], b["rows"])):
            require(first["coordinate"] == second["coordinate"] and set(first["values"]) == set(second["values"]), "comparison axes differ")
            for metric, va in first["values"].items():
                vb = second["values"][metric]
                if va["status"] != 0 or vb["status"] != 0:
                    failures.append({"family": key[0], "case": key[1], "row": i, "metric": metric, "cause": "native refusal", "default": va, "refined": vb})
                    continue
                x, y = va["value"], vb["value"]
                require(type(x) in (int, float) and type(y) in (int, float) and math.isfinite(x) and math.isfinite(y), "nonfinite accepted native metric")
                absolute = abs(x - y)
                scale = max(abs(x), abs(y))
                relative = gate["density_mass_lens_relative"] if key[0] in ("nfw", "hernquist") else gate["relative_difference"]
                allowance = relative * scale
                if metric == "w_phi":
                    allowance = gate["absolute_w_phi"]
                elif metric.endswith("_Mpc"):
                    allowance += gate["distance_absolute_mpc"]
                elif not scale:
                    allowance = gate["scalar_absolute_floor"]
                # Residuals are cancellation diagnostics, not positive physical quantities.
                if metric.endswith("residual"):
                    allowance = gate["scalar_absolute_floor"]
                item = {"family": key[0], "case": key[1], "row": i, "metric": metric, "absolute_difference": absolute, "allowance": allowance, "passed": absolute <= allowance}
                comparisons.append(item)
                if not item["passed"]:
                    failures.append(item)
    require(report["controls"], "reference/refusal controls missing")
    for control in report["controls"]:
        if control["passed"] is not True:
            failures.append({"cause": "native control failed", "control": control})
    return {"status": "passed_empirical_comparison" if not failures else "rejected_or_incomplete",
            "comparisons": comparisons, "failures": failures, "certified_error_bound": None,
            "inference": "not_performed", "observational_qualification": "not_claimed"}


def run_process(argv, root, limits, name):
    def child_limits():
        resource.setrlimit(resource.RLIMIT_AS, (limits["address_bytes"], limits["address_bytes"]))
        resource.setrlimit(resource.RLIMIT_CPU, (limits["wall_seconds"], limits["wall_seconds"]))
        resource.setrlimit(resource.RLIMIT_FSIZE, (limits["stdout_bytes"], limits["stdout_bytes"]))
    started = time.monotonic()
    with (root / (name + ".stdout")).open("xb") as out, (root / (name + ".stderr")).open("xb") as err:
        result = subprocess.run(argv, stdout=out, stderr=err, timeout=limits["wall_seconds"],
                                env={**os.environ, **ENV}, preexec_fn=child_limits)
    record = {"argv": argv, "returncode": result.returncode, "wall_seconds": time.monotonic() - started,
              "threads": ENV, "stdout": pin(root / (name + ".stdout"), limits["stdout_bytes"]),
              "stderr": pin(root / (name + ".stderr"), limits["stdout_bytes"])}
    write(root / (name + ".process.json"), record)
    require(result.returncode == 0, name + " refused; raw process outputs retained")
    return record


def execute(sdk, engine, build_manifest, attempt, profile):
    attempt = clean_path(attempt)
    require(attempt.is_relative_to(ROOT / "results") and not attempt.exists(), "fresh ignored attempt required")
    attempt.parent.mkdir(parents=True, exist_ok=True)
    clean_path(attempt.parent)
    attempt.mkdir(mode=0o700)
    record = {"schema": "native-model-campaign-attempt/v1", "status": "failed", "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "profile": profile, "errors": [], "scientific_role": "synthetic_and_conditional_predictions", "observations": None, "inference": None}
    try:
        request = strict_json((FOLDER / "request.json").read_text())
        require(profile in request["profiles"], "unknown campaign profile")
        record["request"] = pin(FOLDER / "request.json")
        record["source_before"] = source_state(ROOT)
        record["sdk_before"] = sdk_state(sdk, engine, build_manifest, request)
        for name in ("request.json", "consumer.cpp", "controller.py", "experiment.json"):
            (attempt / name).write_bytes((FOLDER / name).read_bytes())
        (attempt / "build-manifest.snapshot.json").write_bytes(Path(build_manifest).read_bytes())
        compiler = Path(shutil.which("c++")).resolve(strict=True)
        record["compiler"] = {"identity": pin(compiler), "version": subprocess.check_output([str(compiler), "--version"], text=True).splitlines()[0]}
        binary = attempt / "native-consumer"
        argv = [str(compiler), "-std=c++20", "-O2", "-Wall", "-Wextra", "-Wpedantic", "-Werror", "-fno-fast-math", "-ffp-contract=off", '-DCAMPAIGN_BUILD_ID="' + request["sdk_pin"]["build_id"] + '"', '-DCAMPAIGN_REQUEST_SHA="' + record["request"]["sha256"] + '"', "-I", str(clean_path(sdk) / "include"), str(FOLDER / "consumer.cpp"), str(clean_path(sdk) / "lib/libirred_core.a"), "-o", str(binary)]
        record["compile"] = run_process(argv, attempt, request["limits"], "compile")
        record["binary"] = pin(binary)
        record["execution"] = run_process([str(binary), profile], attempt, request["limits"], "native")
        report = strict_json((attempt / "native.stdout").read_text())
        record["numerical"] = qualification(report, request, profile)
        write(attempt / "qualification.json", record["numerical"])
        record["sdk_after"] = sdk_state(sdk, engine, build_manifest, request)
        record["source_after"] = source_state(ROOT)
        require(record["sdk_before"] == record["sdk_after"] and record["source_before"] == record["source_after"], "terminal SDK/source drift")
        record["status"] = "completed"
    except Exception as exc:
        record["errors"].append({"kind": type(exc).__name__, "message": str(exc)[:2048]})
    finally:
        record["completed_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        record["files"] = [{**pin(path), "relative_path": str(path.relative_to(attempt))} for path in sorted(attempt.rglob("*")) if path.is_file()]
        require(sum(row["bytes"] for row in record["files"]) <= 33554432, "attempt byte cap")
        write(attempt / "manifest.json", record)
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk", type=Path, required=True)
    parser.add_argument("--engine-source", type=Path, required=True)
    parser.add_argument("--build-manifest", type=Path, required=True)
    parser.add_argument("--attempt", type=Path, required=True)
    parser.add_argument("--profile", choices=("quick", "broader"), default="quick")
    args = parser.parse_args()
    result = execute(args.sdk, args.engine_source, args.build_manifest, args.attempt, args.profile)
    print(json.dumps({"status": result["status"], "errors": result["errors"], "numerical_status": result.get("numerical", {}).get("status")}))
    raise SystemExit(result["status"] != "completed" or result.get("numerical", {}).get("status") != "passed_empirical_comparison")
