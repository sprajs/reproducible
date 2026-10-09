"""Bounded experiment-specific inference owner for the new primary target."""
import argparse
import datetime
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time

import adapter

ROOT = Path(__file__).resolve().parents[2]
# Frozen CLASS parallel.h honours OMP_NUM_THREADS for its pthread TaskSystem.
# Set before importing any compiled solver or BLAS-dependent inference package.
THREAD_ENV = {name: "1" for name in
              ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")}
os.environ.update(THREAD_ENV)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def file_pins(document):
    """Traverse a runtime inventory, never treating a locator as verification."""
    rows = {}
    def visit(value):
        if type(value) is dict:
            if {"path", "bytes", "sha256"} <= set(value) and Path(value["path"]).is_absolute():
                row = {k: value[k] for k in ("path", "bytes", "sha256")}
                if row["path"] in rows and rows[row["path"]] != row:
                    raise ValueError("conflicting runtime file identities")
                rows[row["path"]] = row
            for item in value.values():
                visit(item)
        elif type(value) is list:
            for item in value:
                visit(item)
    visit(document)
    return list(rows.values())


def validate_contract(contract):
    if (contract.get("schema") != "planck-primary-reference-contract/v1"
            or contract.get("status") != "reviewed"
            or not contract.get("candidate_identity")):
        raise ValueError("reviewed immutable source candidate/contract required")
    if contract.get("coordinates") != list(adapter.COORDINATES):
        raise ValueError("exact physical seven-coordinate measure required")
    if contract.get("measure") != "domega_b domega_cdm dH0 dlogA dn_s dtau_reio dA_planck":
        raise ValueError("this adapter requires the explicitly declared H0-flat measure")
    if set(contract["bounds"]) != set(adapter.COORDINATES):
        raise ValueError("all and only seven support bounds required")
    for name, bounds in contract["bounds"].items():
        if (type(bounds) is not list or len(bounds) != 2
                or any(type(v) not in (int, float) or not math.isfinite(v) for v in bounds)
                or not bounds[0] < bounds[1]):
            raise ValueError("finite ordered bounds required for " + name)
    if contract["bounds"]["A_planck"][0] <= 0:
        raise ValueError("positive calibration support required")
    if contract["calibration_prior"]["kind"] != "truncated_normal_in_dA_planck":
        raise ValueError("explicit normalized bounded calibration prior required")
    if contract["likelihood_components"] != ["commander_TT", "simall_EE", "plik_lite_TTTEEE"]:
        raise ValueError("exact released primary target required")
    if contract.get("physical_indicator") != "CLASS_Omega_Lambda_nonnegative":
        raise ValueError("explicit source-owned nonnegative-Lambda physical support required")
    return contract


class Evaluator:
    """Sole physical support owner; native failures abort the caller."""
    def __init__(self, contract, theory, primary, journal, deadline):
        self.contract, self.theory, self.primary = contract, theory, primary
        self.journal, self.deadline, self.count = journal, deadline, 0
        from scipy.stats import truncnorm, uniform
        cp = contract["calibration_prior"]
        lo, hi = contract["bounds"]["A_planck"]
        self.calibration = truncnorm((lo-cp["mean"])/cp["sigma"],
                                    (hi-cp["mean"])/cp["sigma"], loc=cp["mean"], scale=cp["sigma"])
        self.uniforms = [uniform(loc=lo, scale=hi-lo) for name in adapter.COORDINATES[:-1]
                         for lo, hi in [contract["bounds"][name]]]

    def event(self, value):
        self.journal.write(json.dumps(value, sort_keys=True, allow_nan=False) + "\n")
        self.journal.flush()
        os.fsync(self.journal.fileno())

    def score(self, values, *, precision=None):
        values = [float(v) for v in values]
        p = adapter.point(values)
        if self.count >= self.contract["limits"]["max_evaluations"] or time.monotonic() >= self.deadline:
            raise RuntimeError("predeclared attempt work/deadline bound reached")
        self.count += 1
        row = {"evaluation": self.count, "point": p, "policy": precision or self.contract["production_policy"]}
        if not adapter.physical_support(values, self.contract):
            self.event({**row, "status": "physical_prior_excluded"})
            return {"status": "physical_prior_excluded", "logtarget": None}
        self.event({**row, "status": "started"})
        signal.setitimer(signal.ITIMER_REAL, min(self.contract["limits"]["evaluation_wall_seconds"],
                                               self.deadline-time.monotonic()))
        try:
            theory = self.theory.evaluate(values, precision=precision)
            if theory["status"] == "physical_prior_excluded":
                row.update(theory)
                row["logtarget"] = None
                self.event(row)
                return row
            likelihood = self.primary.evaluate(theory["spectra"], p["A_planck"])
            prior_terms = {name: float(owner.logpdf(value)) for name, owner, value in
                           zip(adapter.COORDINATES[:-1], self.uniforms, values[:-1])}
            prior_terms["A_planck"] = float(self.calibration.logpdf(values[-1]))
            prior = math.fsum(prior_terms.values())
            target = prior + likelihood["loglike"]
            if not math.isfinite(target):
                raise ValueError("nonfinite target inside admitted prior support")
            row.update(status="completed", likelihood=likelihood, logprior=prior,
                       prior_terms=prior_terms, logtarget=target, derived=theory["derived"],
                       theory_seconds=theory["seconds"], theory_cache_reused=theory["cache_reused"])
            self.event(row)
            return row
        except BaseException as exc:
            self.event({**row, "status": "likelihood_unsupported" if isinstance(exc, adapter.LikelihoodUnsupported)
                        else "numerical_refused", "error": str(exc)[:4096],
                        "native_record": getattr(exc, "record", None)})
            raise
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def logtarget(self, values):
        row = self.score(values)
        return -math.inf if row["status"] == "physical_prior_excluded" else row["logtarget"]


def execute(args):
    started = time.monotonic()
    contract = validate_contract(json.loads(Path(args.contract).read_bytes()))
    limits = contract["limits"]
    deadline = started + limits["attempt_wall_seconds"]
    attempt = Path(args.attempt).absolute()
    if not attempt.is_relative_to(ROOT / "results") or any(p.is_symlink() for p in attempt.parents):
        raise ValueError("fresh nonsymlink ignored results path required")
    attempt.mkdir(parents=True, exist_ok=False)
    record = {"schema": "planck-primary-reference-attempt/v1", "status": "failed",
              "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "mode": args.mode, "contract": contract, "thread_environment": THREAD_ENV,
              "physical_conditioning_normalization": None, "inference_qualified": False}
    def identity(path):
        raw = Path(path).read_bytes()
        return {"path": str(Path(path).absolute()), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    try:
        dirty = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True)
        if dirty:
            raise ValueError("clean committed experiment source required")
        record["source_revision"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        record["source_files"] = [identity(p) for p in
                                  [Path(__file__), Path(adapter.__file__), ROOT / "experiments/lcdm-reference/likelihood.py",
                                   ROOT / "experiments/lcdm-reference/official_clik.py", ROOT / "experiments/lcdm-reference/score.py"]]
        runtime = json.loads(Path(args.runtime).read_bytes())
        compiled = json.loads(Path(args.classy_runtime).read_bytes())
        record["runtime"] = identity(args.runtime)
        record["classy_runtime"] = identity(args.classy_runtime)
        if runtime["schema"] != "observational-cosmology-runtime/v1" or compiled["status"] != "completed":
            raise ValueError("complete original PLC and new compiled CLASS runtime required")
        score = load("reference_admission", ROOT / "experiments/lcdm-reference/score.py")
        pins = file_pins([runtime, compiled])
        for pin in pins:
            score.checked_file(pin, deadline)
        manifest = json.loads(Path(compiled["source_manifest"]["path"]).read_bytes())
        for pin in manifest["source_files"]:
            absolute = {**pin, "path": str(Path(compiled["source_root"]) / pin["path"])}
            score.checked_file(absolute, deadline)
            pins.append(absolute)
        planck = runtime["planck"]
        roots = [Path(planck["plc_root"]) / relative for _, relative in score.PRODUCTS]
        products = [p for p in planck["admission_files"] if any(root in Path(p["path"]).parents for root in roots)]
        score.product_tree(planck["plc_root"], products, deadline)
        sys.path.insert(0, str(Path(compiled["extension"]["path"]).parent))
        import classy
        if Path(classy.__file__).resolve() != Path(compiled["extension"]["path"]).resolve():
            raise ValueError("loaded CLASS extension path differs")
        clik = load("clik", ROOT / "experiments/lcdm-reference/official_clik.py")
        record["c_api"] = clik.configure(planck["library"])
        likelihood = load("varied_primary_transport", ROOT / "experiments/lcdm-reference/likelihood.py")
        primary = score.initialization(lambda: adapter.PrimaryOwner(likelihood, planck["plc_root"]),
                                       attempt, None, clik, deadline)
        checks = score.selfchecks((attempt / "initialization.stdout.log").read_bytes(),
                                  planck["plc_root"], score.SELFCHECK_CRITERION)
        record["selfchecks"] = checks
        if not all(row["passed"] for row in checks):
            raise ValueError("official initialization selfchecks refused")
        resource.setrlimit(resource.RLIMIT_AS, (limits["address_bytes"], limits["address_bytes"]))
        with (attempt / "evaluations.jsonl").open("x") as journal:
            evaluator = Evaluator(contract, adapter.ClassOwner(classy, contract), primary, journal, deadline)
            if args.mode == "points":
                values = json.loads(Path(args.points).read_bytes())
                record["points_identity"] = identity(args.points)
                record["scores"] = [evaluator.score(p["values"], precision=p.get("policy")) for p in values]
            else:
                raise ValueError("inference execution requires separately reviewed numerical qualification")
        record["cleanup"] = clik.close_all()
        for pin in pins:
            score.checked_file(pin, deadline)
        score.product_tree(planck["plc_root"], products, deadline)
        record.update(status="completed", evaluations=evaluator.count)
    except BaseException as exc:
        record["error"] = {"kind": type(exc).__name__, "message": str(exc)[:4096],
                           "native_record": getattr(exc, "record", None)}
        raise
    finally:
        record["elapsed_seconds"] = time.monotonic()-started
        (attempt / "attempt.json").write_text(json.dumps(record, sort_keys=True, indent=2, allow_nan=False)+"\n")
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("contract", "runtime", "classy-runtime", "attempt", "points"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--mode", choices=("points",), default="points")
    execute(parser.parse_args())
