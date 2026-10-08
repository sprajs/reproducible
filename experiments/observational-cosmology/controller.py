"""A bounded conditional H0 fit using emitted CLASS products and native Gaussian.

No background, ruler, CMB or Gaussian physics is implemented in this controller.
The DESI compression and separate optional official Planck score are distinct.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]


def local_module(name, relative, *, theory_binding=None, bao_binding=None):
    """Avoid generic `run`/`theory` module collisions with other consumers."""
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location("observational_" + name, path)
    module = importlib.util.module_from_spec(spec)
    original = sys.modules.get("theory")
    old_bao = sys.modules.get("bao")
    try:
        if theory_binding is not None:
            sys.modules["theory"] = theory_binding
        if bao_binding is not None:
            sys.modules["bao"] = bao_binding
        spec.loader.exec_module(module)
    finally:
        if theory_binding is not None:
            if original is None:
                sys.modules.pop("theory", None)
            else:
                sys.modules["theory"] = original
        if bao_binding is not None:
            if old_bao is None:
                sys.modules.pop("bao", None)
            else:
                sys.modules["bao"] = old_bao
    return module


theory = local_module("theory", "experiments/lcdm-reference/theory.py")
transport = local_module("transport", "experiments/lcdm-reference/run.py", theory_binding=theory)
bao = local_module("bao", "experiments/lcdm-bao-reference/bao.py", theory_binding=theory)
native_transport = local_module("native_transport", "experiments/lcdm-bao-reference/transport.py", bao_binding=bao)
score_admission = local_module("score_admission", "experiments/lcdm-reference/score.py")

PROFILES = {
    "quick": {"grid_count": 9, "h0_tolerance": 0.05, "max_refinements": 20},
    "broader": {"grid_count": 31, "h0_tolerance": 0.01, "max_refinements": 28},
}
MODELS = ("lcdm", "constant-w")
SDK_REVISION = "7a006f81a36a70cdcd3187a1298a8a1ea2cf3f39"
LIMITS = {"case_wall_seconds": 180, "case_cpu_seconds": 180,
          "total_wall_seconds": 3600, "address_bytes": 2147483648,
          "attempt_bytes": 2147483648, "combined_logs_bytes": 16777216,
          "file_bytes": 134217728, "max_files": 8192, "max_table_rows": 100000}
SOURCE_PATHS = (
    "experiments/observational-cosmology/controller.py",
    "experiments/observational-cosmology/design.json",
    "experiments/observational-cosmology/candidate.json",
    "experiments/observational-cosmology/acquire.py",
    "experiments/lcdm-reference/run.py", "experiments/lcdm-reference/theory.py",
    "experiments/lcdm-reference/reference.json", "scripts/bootstrap_cosmology.py",
    "experiments/lcdm-reference/likelihood.py", "experiments/lcdm-reference/official_clik.py",
    "experiments/lcdm-reference/score.py", "experiments/lcdm-bao-reference/bao.py",
    "experiments/lcdm-bao-reference/consumer.cpp",
    "experiments/lcdm-bao-reference/transport.py",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def pin(path):
    path = Path(path).resolve(strict=True)
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": digest}


def json_new(path, value):
    return transport.write_new(path, transport.json_bytes(value))


def parameters(model, h0, *, full=False):
    require(model in MODELS and type(h0) in (float, int) and math.isfinite(h0)
            and 55 <= h0 <= 85, "model/H0 bounded domain")
    result = theory.class_parameters()
    result["H0"] = format(h0, ".17g")
    if model == "constant-w":
        # CLASS infers its missing dark-energy fluid density from closure.
        del result["Omega_fld"]
        result.update({"Omega_Lambda": "0", "fluid_equation_of_state": "CLP",
                       "w0_fld": "-0.9", "wa_fld": "0", "cs2_fld": "1",
                       "use_ppf": "yes", "c_gamma_over_c_fld": "0.4"})
    if not full:
        # CLASS rejects any present non-linear key without perturbations,
        # including the string "none". Omission selects its source default.
        del result["non linear"]
        result.update({"output": "", "lensing": "no",
                       "write_thermodynamics": "no"})
    return result


def select_data(data, indices):
    """One simultaneous row/column principal submatrix; never diagonalize."""
    require(type(indices) is list and indices and all(type(i) is int for i in indices)
            and indices == sorted(set(indices)) and 0 <= indices[0]
            and indices[-1] < len(data["rows"]), "ordered unique covariance selection")
    return {"rows": [data["rows"][i] for i in indices],
            "covariance": [[data["covariance"][i][j] for j in indices] for i in indices],
            "source_indices": indices,
            "selection": "same ordered principal submatrix on both covariance axes"}


def render_input(model, h0, output_root, *, full=False):
    """Render this declared domain without weakening the frozen reference adapter."""
    physical = parameters(model, h0, full=full)
    root = str(Path(output_root).absolute())
    require(not any(c in root for c in "\n\r\x00#=") and len(root.encode()) <= 400, "CLASS output root syntax")
    require(all(not any(c in key + value for c in "\n\r\x00=")
                for key, value in physical.items()), "CLASS parameter syntax")
    lines = [key + " = " + value for key, value in physical.items()]
    return ("\n".join([*lines, "root = " + root]) + "\n").encode("ascii")


def fit_profile(evaluate, profile, lower=55.0, upper=85.0):
    """Deterministic grid-bracketed golden search; report its finite resolution."""
    require(profile in PROFILES, "unknown profile")
    policy = PROFILES[profile]
    cache = {}
    def score(x):
        key = format(x, ".17g")
        if key not in cache:
            value = evaluate(x)
            require(type(value) in (float, int) and math.isfinite(value), "finite fit score")
            cache[key] = {"H0": x, "chi2": float(value)}
        return cache[key]["chi2"]
    grid = [lower + (upper - lower) * i / (policy["grid_count"] - 1)
            for i in range(policy["grid_count"])]
    scores = [score(x) for x in grid]
    best = min(range(len(grid)), key=lambda i: (scores[i], i))
    require(0 < best < len(grid) - 1, "grid optimum lies at search boundary; extend reviewed domain")
    left, right = grid[best - 1], grid[best + 1]
    ratio = (math.sqrt(5.0) - 1.0) / 2.0
    x1, x2 = right - ratio * (right - left), left + ratio * (right - left)
    f1, f2 = score(x1), score(x2)
    refinements = 0
    while right - left > policy["h0_tolerance"] and refinements < policy["max_refinements"]:
        if f1 <= f2:
            right, x2, f2 = x2, x1, f1
            x1 = right - ratio * (right - left)
            f1 = score(x1)
        else:
            left, x1, f1 = x1, x2, f2
            x2 = left + ratio * (right - left)
            f2 = score(x2)
        refinements += 1
    require(right - left <= policy["h0_tolerance"], "optimizer refinement budget exhausted")
    score((left + right) / 2.0)
    selected = min(cache.values(), key=lambda row: (row["chi2"], row["H0"]))
    return {"best_evaluated": selected, "final_search_bracket": [left, right],
            "search_width_km_s_Mpc": right - left, "refinements": refinements,
            "points": sorted(cache.values(), key=lambda row: row["H0"]),
            "grid": grid, "policy": policy,
            "scope": "bounded conditional likelihood minimum; not global proof or posterior",
            "uncertainty_interval": None, "prior": None}


def source_state():
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    dirty = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=normal"],
                                    cwd=ROOT, text=True)
    require(not dirty, "run requires clean committed Reproducible source")
    return {"revision": revision, "dirty": False, "files": [pin(ROOT / p) for p in SOURCE_PATHS]}


def verify_runtime(runtime, deadline):
    require(type(runtime) is dict and {"class", "gaussian", "bootstrap_source"} <= set(runtime)
            and runtime.get("schema") == "observational-cosmology-runtime/v1", "runtime engines/schema required")
    require(all(runtime["bootstrap_source"][k] == pin(ROOT / "scripts/bootstrap_cosmology.py")[k]
                for k in ("bytes", "sha256")),
            "actual reviewed bootstrap source identity")
    transport.file_bytes(runtime["bootstrap_source"]["path"], 262144, runtime["bootstrap_source"])
    require(all(runtime["bootstrap_snapshot"][k] == runtime["bootstrap_source"][k]
                for k in ("bytes", "sha256")), "retained executed bootstrap source snapshot")
    transport.file_bytes(runtime["bootstrap_snapshot"]["path"], 262144, runtime["bootstrap_snapshot"])
    class_files = transport.engine_identities(runtime["class"], deadline)
    require(type(runtime.get("class_dependencies")) is list and runtime["class_dependencies"],
            "actual CLASS dependency inventory required")
    for item in runtime["class_dependencies"]:
        _, actual = transport.file_bytes(item["path"], 134217728, item)
        class_files.append(actual)
    gaussian = runtime["gaussian"]
    require({"binary", "sdk_build_id", "source_revision", "consumer_source", "build_receipt",
             "sdk_inventory"} <= set(gaussian), "complete native Gaussian build identity")
    require(all(gaussian["consumer_source"][k] == pin(ROOT / "experiments/lcdm-bao-reference/consumer.cpp")[k]
                for k in ("bytes", "sha256")),
            "exact existing reviewed native consumer source")
    transport.file_bytes(gaussian["consumer_source"]["path"], 262144, gaussian["consumer_source"])
    require(len(gaussian["sdk_build_id"]) == 64
            and all(c in "0123456789abcdef" for c in gaussian["sdk_build_id"]), "native SDK build identity")
    require(gaussian["source_revision"] == SDK_REVISION, "pinned reviewed native SDK source")
    native_files = []
    for item in [gaussian["binary"], gaussian["build_receipt"], *gaussian["sdk_inventory"]]:
        _, actual = transport.file_bytes(item["path"], 134217728, item)
        native_files.append(actual)
    planck_files = []
    if runtime.get("planck"):
        planck = runtime["planck"]
        require({"library", "plc_root", "admission_files", "build_receipt"} <= set(planck),
                "complete official likelihood runtime identity")
        for item in [planck["library"], planck["build_receipt"], *planck["admission_files"]]:
            _, actual = transport.file_bytes(item["path"], 2147483648, item)
            planck_files.append(actual)
        tree = planck_product_tree(planck, deadline)
    else:
        tree = None
    return {"class": class_files, "gaussian": native_files, "planck": planck_files,
            "planck_product_tree": tree}


def planck_product_tree(planck, deadline):
    roots = [Path(planck["plc_root"]) / relative for _, relative in score_admission.PRODUCTS]
    selected = [item for item in planck["admission_files"]
                if any(root in Path(item["path"]).parents for root in roots)]
    return score_admission.product_tree(planck["plc_root"], selected, deadline)


def gaussian_score(runtime, data, prediction, directory):
    request = native_transport.make_input(data, [prediction])
    transport.write_new(directory / "gaussian-input.txt", request)
    env = {**os.environ, **{k: "1" for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                                             "MKL_NUM_THREADS", "BLIS_NUM_THREADS")}}
    process = {"argv": [runtime["binary"]["path"]], "timeout_seconds": 30, "status": "started"}
    json_new(directory / "gaussian-started.json", process)
    try:
        result = subprocess.run(process["argv"], input=request, capture_output=True,
                                timeout=30, env=env)
    except subprocess.TimeoutExpired as exc:
        transport.write_new(directory / "gaussian.stdout.json", exc.stdout or b"")
        transport.write_new(directory / "gaussian.stderr.log", exc.stderr or b"")
        json_new(directory / "gaussian-process.json", {**process, "status": "timed_out", "returncode": None})
        raise
    json_new(directory / "gaussian-process.json", {**process, "status": "completed", "returncode": result.returncode})
    transport.write_new(directory / "gaussian.stdout.json", result.stdout)
    transport.write_new(directory / "gaussian.stderr.log", result.stderr)
    require(len(result.stdout) <= 1048576 and len(result.stderr) <= 1048576,
            "native Gaussian output bound")
    record = native_transport.admit_output(result.stdout, data, [prediction], runtime["sdk_build_id"])
    require(result.returncode == 0 and record["status"] == "accepted", "native Gaussian refused")
    return record


def parameter_consumption(raw, physical, *, full):
    unused = {}
    for line in raw.decode("ascii").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, value = [part.strip() for part in line.split("=", 1)]
        require(key in physical and key not in unused and value == physical[key],
                "unconsumed parameter/value differs from supplied request")
        unused[key] = value
    allowed = set() if full else {"modes", "ic", "l_max_scalars", "P_k_max_1/Mpc", "z_pk"}
    require(set(unused) <= allowed, "unconsumed physical/fluid control refused")
    return {"status": "passed", "unused": unused, "allowed_unused": sorted(allowed),
            "physical_and_fluid_controls": "all consumed"}


def class_case(engine, model, h0, directory, attempt, deadline, *, full=False):
    directory.mkdir(mode=0o700)
    physical = parameters(model, h0, full=full)
    ini = transport.write_new(directory / "input.ini", render_input(model, h0, directory / "class", full=full))
    process = transport.run_class([engine["binary"]["path"], ini["path"]], engine["source_root"],
                                  directory, attempt, LIMITS, deadline, LIMITS["combined_logs_bytes"])
    json_new(directory / "process.json", process)
    require(process["status"] == "completed", "CLASS failed; raw process/streams retained")
    unused_raw, unused_pin = transport.file_bytes(directory / "class_unused_parameters", 65536)
    consumption = parameter_consumption(unused_raw, physical, full=full)
    json_new(directory / "parameter-consumption.json", {**consumption, "source_identity": unused_pin})
    if full:
        products, state = transport.products(directory, physical, LIMITS, engine["binary"])
        for point in products["background"]:
            point["DM_scope"] = "flat-FLRW: transverse equals radial"
        json_new(directory / "products.json", products)
    else:
        raw, background_pin = transport.file_bytes(directory / "class_background.dat", LIMITS["file_bytes"])
        log, log_pin = transport.file_bytes(directory / "stdout.log", LIMITS["combined_logs_bytes"])
        state = {"parameters": physical, "background": theory.parse_table(raw),
                 "drag": theory.predicted_drag(log),
                 "source_identities": {"background": background_pin, "stdout": log_pin,
                                       "binary": engine["binary"], "input_ini": ini}}
        products = None
    columns = state["background"]["columns"]
    density = "(.)rho_fld" if model == "constant-w" else "(.)rho_lambda"
    require(density in columns and "(.)rho_crit" in columns, "emitted dark-energy closure columns")
    today = [row for row in state["background"]["rows"] if row[columns.index("z")] == 0]
    require(len(today) == 1, "unique emitted present-day closure row")
    rho, critical = today[0][columns.index(density)], today[0][columns.index("(.)rho_crit")]
    require(rho > 0 and critical > 0, "nonpositive inferred dark-energy closure")
    json_new(directory / "closure.json", {"source": "emitted CLASS present-day density columns",
             "density_column": density, "rho": rho, "rho_critical": critical,
             "inferred_density_fraction": rho / critical, "positive": True})
    return products, state


def score_planck(runtime, products, directory, owner, deadline, likelihood, score):
    configuration = {"backend": "clik", "highl": "plik_lite_TTTEEE",
                     "plc_root": runtime["plc_root"], "nuisance": {"A_planck": 1.0},
                     "calibration_prior": {"convention": "relative_penalty"}}
    score.arm(deadline)
    try:
        return likelihood.evaluate(products["cmb"], configuration, directory, owner=owner)
    finally:
        score.disarm()


def execute(runtime_path, attempt_path, profile, deadline_utc, *, planck=False):
    attempt = Path(attempt_path).absolute()
    require(".." not in attempt.parts, "invalid attempt path")
    for parent in reversed(attempt.parents):
        require(not parent.is_symlink(), "attempt ancestor symlink")
        if not parent.exists():
            parent.mkdir(mode=0o700)
        require(parent.is_dir(), "attempt ancestor not a directory")
    attempt = transport.path_without_symlinks(attempt)
    attempt.mkdir(mode=0o700)
    record = {"schema": "observational-cosmology-attempt/v1", "status": "failed",
              "runtime": None, "profile": profile, "models": {}, "errors": [],
              "probe_combination": None, "observations": "DESI DR2 released Gaussian compression",
              "gates": {"execution": "unassessed", "native_numerical": "unassessed",
                        "conditional_fit": "unassessed", "posterior": "not_requested",
                        "joint_inference": "not_requested"},
              "synthetic_controls": "unit tests only; excluded from observational score"}
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "BLIS_NUM_THREADS",
                 "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[name] = "1"
    record["parent_thread_environment"] = {name: os.environ[name] for name in
        ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "BLIS_NUM_THREADS",
         "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS")}
    owner = official = None
    runtime = None
    deadline = time.monotonic() + 180
    started = time.monotonic()
    try:
        runtime, runtime_pin, raw_runtime = transport.load_json(runtime_path)
        record["runtime"] = runtime_pin
        deadline_time = datetime.datetime.fromisoformat(deadline_utc)
        require(deadline_time.tzinfo is not None, "deadline requires UTC offset")
        remaining = (deadline_time - datetime.datetime.now(datetime.timezone.utc)).total_seconds()
        require(3 < remaining <= 14400 and profile in PROFILES, "expired/excessive deadline or profile")
        deadline = time.monotonic() + min(remaining, LIMITS["total_wall_seconds"])
        record["source_before"] = source_state()
        transport.write_new(attempt / "runtime.snapshot.json", raw_runtime)
        design, _, design_raw = transport.load_json(ROOT / "experiments/observational-cosmology/design.json")
        require(design["fit"]["profiles"] == PROFILES and design["fit"]["selection_indices"] == list(range(13)),
                "declared profile/selection differs from controller")
        transport.write_new(attempt / "design.snapshot.json", design_raw)
        candidate, candidate_pin, candidate_raw = transport.load_json(ROOT / "experiments/observational-cosmology/candidate.json")
        require(candidate_pin["sha256"] == design["candidate_source"]["sha256"]
                and candidate["kind"] == "candidate_design", "source candidate intake binding")
        transport.write_new(attempt / "candidate.snapshot.json", candidate_raw)
        record["runtime_before"] = verify_runtime(runtime, deadline)
        data = bao.read_data(str(ROOT))
        selection = select_data(data, list(range(13)))
        record["selection"] = selection
        record["data_before"] = data["source_identities"]
        json_new(attempt / "data.snapshot.json", data)
        if planck:
            require(runtime.get("planck") is not None, "official Planck runtime unavailable")
            official = local_module("official_clik", "experiments/lcdm-reference/official_clik.py")
            likelihood = local_module("likelihood", "experiments/lcdm-reference/likelihood.py")
            score = local_module("score", "experiments/lcdm-reference/score.py")
            official.configure(runtime["planck"]["library"])
            sys.modules["clik"] = official
            config = {"backend": "clik", "highl": "plik_lite_TTTEEE",
                      "plc_root": runtime["planck"]["plc_root"], "nuisance": {"A_planck": 1.0},
                      "calibration_prior": {"convention": "relative_penalty"}}
            owner = score.initialization(lambda: likelihood.prepare(config), attempt, transport,
                                         official, deadline)
            checks = score.selfchecks((attempt / "initialization.stdout.log").read_bytes(),
                                      config["plc_root"], score.SELFCHECK_CRITERION)
            require(all(row["passed"] for row in checks), "official likelihood selfcheck failed")
            record["official_selfchecks"] = checks
        for model in MODELS:
            model_dir = attempt / model
            model_dir.mkdir()
            entry = {"status": "started", "evaluations": [], "planck_primary": None}
            record["models"][model] = entry
            def evaluate(h0):
                require(time.monotonic() < deadline - 5, "whole experiment deadline")
                directory = model_dir / f"point-{len(entry['evaluations']):03d}"
                _, state = class_case(runtime["class"], model, h0, directory, attempt, deadline)
                prediction = bao.predict(state, data)
                for row in prediction["rows"]:
                    row["background"]["DM_scope"] = "flat-FLRW: transverse equals radial"
                json_new(directory / "bao-predictions.json", prediction)
                native = gaussian_score(runtime["gaussian"], data, prediction, directory)
                value = native["rows"][0]["payload"]["quadratic"]
                entry["evaluations"].append({"H0": h0, "chi2": value, "directory": str(directory),
                                             "native_receipt": pin(directory / "gaussian.stdout.json")})
                transport.inventory(attempt, LIMITS)
                return value
            entry["fit"] = fit_profile(evaluate, profile)
            best = entry["fit"]["best_evaluated"]
            final = model_dir / "best-fit-products"
            products, state = class_case(runtime["class"], model, best["H0"], final, attempt,
                                          deadline, full=True)
            prediction = bao.predict(state, data)
            for row in prediction["rows"]:
                row["background"]["DM_scope"] = "flat-FLRW: transverse equals radial"
            json_new(final / "bao-predictions.json", prediction)
            native = gaussian_score(runtime["gaussian"], data, prediction, final)
            entry["full_prediction_chi2"] = native["rows"][0]["payload"]["quadratic"]
            entry["output_policy_chi2_difference"] = entry["full_prediction_chi2"] - best["chi2"]
            entry["r_drag_Mpc"] = state["drag"]["r_drag_Mpc"]
            entry["products"] = pin(final / "products.json")
            entry["bao_predictions"] = pin(final / "bao-predictions.json")
            entry["artifact_paths"] = {"products": str((final / "products.json").relative_to(attempt)),
                                       "bao_predictions": str((final / "bao-predictions.json").relative_to(attempt))}
            if owner:
                entry["planck_primary"] = score_planck(runtime["planck"], products, final, owner, deadline,
                                                       likelihood, score)
            entry["status"] = "completed"
        record["gates"].update(execution="passed", native_numerical="passed",
                                conditional_fit="bounded-H0-profile-completed")
        record["status"] = "completed"
    except BaseException as exc:
        record["errors"].append(transport.failure(exc))
        if hasattr(exc, "record"):
            record["errors"][-1]["returned_failure_prefix"] = exc.record
    finally:
        if official:
            try:
                record["official_cleanup"] = official.close_all()
            except BaseException as exc:
                record["errors"].append(transport.failure(exc))
                record["status"] = "failed"
        try:
            record["runtime_after"] = verify_runtime(runtime, deadline)
            record["source_after"] = source_state()
            record["data_after"] = bao.read_data(str(ROOT))["source_identities"]
            require(record.get("runtime_before") == record["runtime_after"]
                    and record.get("source_before") == record["source_after"]
                    and record.get("data_before") == record["data_after"], "terminal source/input drift")
        except BaseException as exc:
            record["errors"].append(transport.failure(exc))
            record["status"] = "failed"
        record["wall_seconds"] = time.monotonic() - started
        try:
            record["inventory"] = transport.seal_inventory(attempt, LIMITS)
        except BaseException as exc:
            record["errors"].append(transport.failure(exc))
            record["inventory"] = {"status": "refused", "files": [], "errors": [transport.failure(exc)],
                                   "full_inventory_available": False}
        if record["inventory"]["errors"]:
            record["status"] = "failed"
        if record["status"] != "completed":
            record["gates"]["execution"] = "failed"
        json_new(attempt / "manifest.json", record)
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--attempt", type=Path, required=True)
    parser.add_argument("--profile", choices=tuple(PROFILES), default="quick")
    parser.add_argument("--deadline-utc", required=True)
    parser.add_argument("--planck", action="store_true")
    args = parser.parse_args()
    result = execute(args.runtime.absolute(), args.attempt.absolute(), args.profile,
                     args.deadline_utc, planck=args.planck)
    print(json.dumps({"status": result["status"], "manifest": str(args.attempt.absolute() / "manifest.json"),
                      "errors": result["errors"]}, indent=2))
    raise SystemExit(0 if result["status"] == "completed" else 1)
