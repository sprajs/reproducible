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
import re
import selectors
import stat
import signal
import subprocess
import struct
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
CONFIG_BYTES = 2097152
# Frozen CLASS parallel.h honours OMP_NUM_THREADS for its pthread TaskSystem.
# Set before importing any compiled solver or BLAS-dependent inference package.
THREAD_ENV = {name: "1" for name in
              ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")}
os.environ.update(THREAD_ENV)


class ResourceInterrupted(BaseException):
    pass


def interrupted(_signal, _frame):
    raise ResourceInterrupted("predeclared evaluation wall limit reached")


def refusal_status(exc):
    if isinstance(exc, adapter.LikelihoodUnsupported):
        return "likelihood_unsupported"
    if isinstance(exc, adapter.NumericalRefusal):
        return "numerical_refused"
    if isinstance(exc, ResourceInterrupted):
        return "resource_interrupted"
    if isinstance(exc, KeyboardInterrupt):
        return "user_interrupted"
    return "software_refused"


def terminal_status(code, failure):
    if failure in ("attempt_wall_seconds", "evaluation_wall_seconds", "attempt_bytes", "logs_bytes", "file_bytes") \
            or code in (-signal.SIGALRM, -signal.SIGXFSZ):
        return "resource_interrupted"
    if failure is not None:
        return failure
    return "completed" if code == 0 else "worker_refused"


def load(name, path):
    import types
    raw = bounded_bytes(path, 262144)
    module = types.ModuleType(name)
    module.__file__, module.__package__ = str(path), ""
    sys.modules[name] = module
    exec(compile(raw, str(path), "exec"), module.__dict__)
    return module


def bounded_bytes(path, limit=CONFIG_BYTES):
    path = Path(path).absolute()
    if any(p.is_symlink() for p in path.parents):
        raise ValueError("input symlink ancestor")
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb") as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
            raise ValueError("input regular-file byte bound")
        raw = stream.read(limit + 1)
        after = os.fstat(stream.fileno())
    facts = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    if len(raw) > limit or facts(before) != facts(after) or facts(after) != facts(path.lstat()):
        raise ValueError("input byte/stat identity changed")
    return raw


def read_json(path):
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ValueError("duplicate JSON key")
            value[key] = item
        return value
    return json.loads(bounded_bytes(path), object_pairs_hook=pairs,
                      parse_constant=lambda _x: (_ for _ in ()).throw(ValueError("nonfinite JSON")))


adapter = load("primary_reference_adapter", Path(__file__).with_name("adapter.py"))


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
    identity = contract["candidate_identity"]
    if (set(identity) != {"repository", "revision", "path", "snapshot", "bytes", "sha256"}
            or identity["repository"] != "sprajs/prospector"
            or re.fullmatch(r"[0-9a-f]{40}", identity["revision"]) is None
            or identity["snapshot"] not in {"candidate.json", "candidate-v2.json"}
            or re.fullmatch(r"[0-9a-f]{64}", identity["sha256"]) is None):
        raise ValueError("exact immutable Prospector candidate identity required")
    snapshot = Path(__file__).parent / identity["snapshot"]
    raw = bounded_bytes(snapshot)
    if len(raw) != identity["bytes"] or hashlib.sha256(raw).hexdigest() != identity["sha256"]:
        raise ValueError("candidate snapshot exact bytes differ")
    candidate = json.loads(raw)
    source_contract = candidate["minimal_test"]["parameter_choices"]["consumer_contract"]
    if any(contract.get(key) != value for key, value in source_contract.items()):
        raise ValueError("consumer physical/prior semantics differ from source candidate")
    bbn = contract["bbn_table"]
    if (set(bbn) != {"path", "bytes", "sha256"} or Path(bbn["path"]).is_absolute()
            or ".." in Path(bbn["path"]).parts
            or contract["class_fixed"]["sBBN file"] != bbn["path"]):
        raise ValueError("source-relative exact BBN table pin required")
    for name in ("max_evaluations", "evaluation_wall_seconds", "attempt_wall_seconds", "address_bytes",
                 "attempt_bytes", "file_bytes", "logs_bytes"):
        if type(contract["limits"][name]) is not int or contract["limits"][name] <= 0:
            raise ValueError("positive integer resource policy required")
    return contract


class Evaluator:
    """Sole physical support owner; native failures abort the caller."""
    def __init__(self, contract, theory, primary, journal, deadline, artifact_root=None):
        self.contract, self.theory, self.primary = contract, theory, primary
        self.journal, self.deadline, self.count = journal, deadline, 0
        self.artifact_root, self.last_artifact = artifact_root, None
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
        row = {"evaluation": self.count, "point": p, "policy": precision or self.contract["production_policy"],
               "started_monotonic": time.monotonic()}
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
            key = tuple(values[:6]), row["policy"]
            if self.last_artifact is not None and self.last_artifact[0] == key:
                artifact = self.last_artifact[1]
            else:
                path = self.artifact_root / (f"theory-{self.count:08d}.binary64")
                order = ["TT", "EE", "BB", "TE"]
                raw = b"".join(struct.pack("<d", value) for name in order for value in theory["spectra"][name])
                with path.open("xb") as stream:
                    stream.write(raw)
                    stream.flush()
                    os.fsync(stream.fileno())
                artifact = {"path": str(path.absolute()), "bytes": len(raw),
                            "sha256": hashlib.sha256(raw).hexdigest(),
                            "encoding": "IEEE754-binary64-little-endian", "unit": "Cl_microkelvin_squared",
                            "spectra_order": order, "ell": [0, self.contract["lmax"]]}
                self.last_artifact = key, artifact
            row.update(derived=theory["derived"], input_parameters=theory["input_parameters"],
                       theory_seconds=theory["seconds"], theory_cache_reused=theory["cache_reused"],
                       theory_artifact=artifact)
            self.event({**row, "status": "theory_completed"})
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
                       input_parameters=theory["input_parameters"],
                       theory_seconds=theory["seconds"], theory_cache_reused=theory["cache_reused"])
            self.event(row)
            return row
        except BaseException as exc:
            self.event({**row, "status": refusal_status(exc), "error": str(exc)[:4096],
                        "native_record": getattr(exc, "record", None)})
            raise
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def logtarget(self, values):
        row = self.score(values)
        return -math.inf if row["status"] == "physical_prior_excluded" else row["logtarget"]


def execute(args):
    started = time.monotonic()
    contract = validate_contract(read_json(args.contract))
    limits = contract["limits"]
    deadline = started + limits["attempt_wall_seconds"]
    attempt = Path(args.attempt).absolute()
    if not attempt.is_relative_to(ROOT / "results") or any(p.is_symlink() for p in attempt.parents):
        raise ValueError("fresh nonsymlink ignored results path required")
    if not args.worker:
        attempt.mkdir(parents=True, exist_ok=False)
    elif not attempt.is_dir():
        raise ValueError("supervisor-created fresh attempt required")
    record = {"schema": "planck-primary-reference-attempt/v1", "status": "failed",
              "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "mode": args.mode, "contract": contract, "thread_environment": THREAD_ENV,
              "physical_conditioning_normalization": contract.get("physical_conditioning_normalization"),
              "inference_qualified": False}
    score, pins, post_error = None, [], None
    def identity(path):
        raw = bounded_bytes(path)
        return {"path": str(Path(path).absolute()), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    try:
        dirty = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True)
        if dirty:
            raise ValueError("clean committed experiment source required")
        record["source_revision"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        packet_files = [p for p in sorted(Path(__file__).parent.iterdir()) if p.is_file()]
        if len(packet_files) > 8 or any(p.is_symlink() for p in packet_files):
            raise ValueError("eight regular source files per packet runtime bound")
        tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
        source_bytes = sum((ROOT / name).stat().st_size for name in tracked if name)
        if source_bytes > 2621440:
            raise ValueError("complete public source tree 2.5MiB bound")
        record["source_budget"] = {"public_bytes": source_bytes, "maximum_public_bytes": 2621440,
                                   "packet_files": len(packet_files), "maximum_packet_files": 8}
        record["source_files"] = [identity(p) for p in
                                  [*packet_files,
                                   ROOT / "experiments/lcdm-reference/likelihood.py",
                                   ROOT / "experiments/lcdm-reference/official_clik.py",
                                   ROOT / "experiments/lcdm-reference/score.py"] if p.is_file()]
        runtime = read_json(args.runtime)
        compiled = read_json(args.classy_runtime)
        record["runtime"] = identity(args.runtime)
        record["classy_runtime"] = identity(args.classy_runtime)
        if runtime["schema"] != "observational-cosmology-runtime/v1" or compiled["status"] != "completed":
            raise ValueError("complete original PLC and new compiled CLASS runtime required")
        score = load("reference_admission", ROOT / "experiments/lcdm-reference/score.py")
        pins = file_pins([runtime, compiled])
        for pin in pins:
            score.checked_file(pin, deadline)
        if Path(compiled["python"]["path"]) != Path("/proc/self/exe").resolve():
            raise ValueError("executing Python differs from new extension build identity")
        manifest = read_json(compiled["source_manifest"]["path"])
        for pin in manifest["source_files"]:
            absolute = {**pin, "path": str(Path(compiled["source_root"]) / pin["path"])}
            score.checked_file(absolute, deadline)
            pins.append(absolute)
        bbn = {**contract["bbn_table"], "path": str(Path(compiled["source_root"]) / contract["bbn_table"]["path"])}
        score.checked_file(bbn, deadline)
        contract = {**contract, "_resolved_bbn_path": bbn["path"],
                    "_resolved_class_source_root": compiled["source_root"]}
        record["resolved_bbn_table"] = bbn
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
        signal.signal(signal.SIGALRM, interrupted)
        checks = score.selfchecks((attempt / "initialization.stdout.log").read_bytes(),
                                  planck["plc_root"], score.SELFCHECK_CRITERION)
        record["selfchecks"] = checks
        if not all(row["passed"] for row in checks):
            raise ValueError("official initialization selfchecks refused")
        resource.setrlimit(resource.RLIMIT_AS, (limits["address_bytes"], limits["address_bytes"]))
        with (attempt / "evaluations.jsonl").open("x") as journal:
            evaluator = Evaluator(contract, adapter.ClassOwner(classy, contract), primary, journal, deadline,
                                  artifact_root=attempt)
            if args.mode == "points":
                values = read_json(args.points)
                if type(values) is not list or len(values) > limits["max_evaluations"]:
                    raise ValueError("ordered point-count resource bound")
                record["points_identity"] = identity(args.points)
                record["scores"] = [evaluator.score(p["values"], precision=p.get("policy")) for p in values]
            else:
                raise ValueError("inference execution requires separately reviewed numerical qualification")
        record["cleanup"] = clik.close_all()
        record.update(status="completed", evaluations=evaluator.count)
    except BaseException as exc:
        record["status"] = refusal_status(exc)
        record["error"] = {"kind": type(exc).__name__, "message": str(exc)[:4096],
                           "native_record": getattr(exc, "record", None)}
        raise
    finally:
        if score is not None:
            try:
                after = [*pins, *record.get("source_files", [])]
                after += [record[key] for key in ("runtime", "classy_runtime", "points_identity") if key in record]
                for pin in after:
                    score.checked_file(pin, deadline)
                if "planck" in locals() and "products" in locals():
                    score.product_tree(planck["plc_root"], products, deadline)
                record["after_admission"] = {"status": "passed", "verified_pins": len(after)}
            except BaseException as verification:
                post_error = verification
                record["after_admission"] = {"status": "refused", "kind": type(verification).__name__,
                    "error": str(verification)[:4096],
                    "observed_identity": getattr(verification, "observed_identity", None),
                    "expected_identity": getattr(verification, "expected_identity", None)}
                if record["status"] == "completed":
                    record["status"] = "software_refused"
        record["elapsed_seconds"] = time.monotonic()-started
        (attempt / "attempt.json").write_text(json.dumps(record, sort_keys=True, indent=2, allow_nan=False)+"\n")
    if post_error is not None:
        raise post_error
    return record


def supervise(command, attempt, limits):
    """One persistent numerical child, with an external native-call watchdog.

    A Python signal cannot reliably interrupt an in-flight Cython/C call. The
    parent monitors fsynced started events and kills/reaps the child's process
    group on either deadline; its terminal record survives a native hang.
    """
    attempt = Path(attempt)
    attempt.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    failure = None
    with (attempt / "worker.stdout.log").open("xb") as stdout, (attempt / "worker.stderr.log").open("xb") as stderr:
        file_limit = limits.get("file_bytes", 134217728)
        log_limit = limits.get("logs_bytes", 16777216)
        attempt_limit = limits.get("attempt_bytes", 2147483648)
        def child_limits():
            resource.setrlimit(resource.RLIMIT_FSIZE, (file_limit, file_limit))
        child = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 start_new_session=True, preexec_fn=child_limits)
        selector = selectors.DefaultSelector()
        selector.register(child.stdout, selectors.EVENT_READ, stdout)
        selector.register(child.stderr, selectors.EVENT_READ, stderr)
        try:
            while child.poll() is None or selector.get_map():
                elapsed = time.monotonic() - started
                if elapsed > limits["attempt_wall_seconds"]:
                    failure = "attempt_wall_seconds"
                files = [p for p in attempt.rglob("*") if p.is_file()]
                sizes = {p: p.stat().st_size for p in files}
                used = sum(sizes.values())
                logs = sum(size for path, size in sizes.items() if path.suffix == ".log")
                if used > attempt_limit - 4096:
                    failure = "attempt_bytes"
                if any(size > file_limit for size in sizes.values()):
                    failure = "file_bytes"
                if logs >= log_limit:
                    failure = "logs_bytes"
                journal = attempt / "evaluations.jsonl"
                if journal.exists():
                    with journal.open("rb") as stream:
                        stream.seek(max(0, journal.stat().st_size - 65536))
                        lines = stream.read(65536).splitlines()
                    if lines:
                        try:
                            last = json.loads(lines[-1])
                        except (ValueError, UnicodeError):
                            last = None  # Partial final line is not an earned event.
                        if (last is not None and last.get("status") in ("started", "theory_completed")
                                and time.monotonic()-last["started_monotonic"] > limits["evaluation_wall_seconds"]):
                            failure = "evaluation_wall_seconds"
                if failure is not None:
                    if child.poll() is None:
                        os.killpg(child.pid, signal.SIGKILL)
                    break
                for key, _events in selector.select(timeout=0.1):
                    remaining = min(log_limit-logs, attempt_limit-used-4096,
                                    file_limit-key.data.tell())
                    if remaining <= 0:
                        failure = "logs_bytes" if logs >= log_limit else "attempt_bytes" if used >= attempt_limit-4096 else "file_bytes"
                        break
                    raw = key.fileobj.read1(min(65536, remaining))
                    if not raw:
                        selector.unregister(key.fileobj)
                        continue
                    key.data.write(raw)
                    key.data.flush()
                    logs += len(raw)
                    used += len(raw)
        except BaseException as exc:
            failure = refusal_status(exc)
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGKILL)
        finally:
            if failure is not None and child.poll() is None:
                os.killpg(child.pid, signal.SIGKILL)
            code = child.wait()
            selector.close()
            child.stdout.close()
            child.stderr.close()
            status = terminal_status(code, failure)
            worker_status = None
            worker_record = attempt / "attempt.json"
            if worker_record.exists() and worker_record.stat().st_size <= 2097152:
                try:
                    worker_status = read_json(worker_record).get("status")
                except (ValueError, UnicodeError):
                    pass
            if status == "worker_refused" and worker_status in {
                    "numerical_refused", "likelihood_unsupported", "software_refused",
                    "resource_interrupted", "user_interrupted"}:
                status = worker_status
            terminal = {"schema": "planck-primary-supervisor-terminal/v1", "status": status,
                        "worker_returncode": code, "resource_limit": failure,
                        "worker_status": worker_status,
                        "elapsed_seconds": time.monotonic()-started,
                        "worker_attempt_record_exists": (attempt / "attempt.json").exists(),
                        "inference_qualified": False}
            with (attempt / "terminal.json").open("x") as stream:
                json.dump(terminal, stream, indent=2, sort_keys=True, allow_nan=False)
                stream.write("\n")
    return terminal


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("contract", "runtime", "classy-runtime", "attempt", "points"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--mode", choices=("points",), default="points")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        execute(args)
    else:
        contract = validate_contract(read_json(args.contract))
        attempt = Path(args.attempt).absolute()
        if not attempt.is_relative_to(ROOT / "results") or any(p.is_symlink() for p in attempt.parents):
            raise ValueError("fresh nonsymlink ignored results path required")
        result = supervise([sys.executable, str(Path(__file__).absolute()), *sys.argv[1:], "--worker"],
                           attempt, contract["limits"])
        print(json.dumps(result, sort_keys=True))
        if result["status"] != "completed":
            sys.exit(1)
