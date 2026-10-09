"""New fully varied primary-CMB adapter; all physics remains in CLASS/PLC.

The caller admits source/build/data identities before constructing either owner.
Historical fixed-point adapters remain unchanged. This route never translates
a native numerical refusal into a prior exclusion.
"""
import math
import time
from pathlib import Path


COORDINATES = ("omega_b", "omega_cdm", "H0", "logA", "n_s", "tau_reio", "A_planck")


class NumericalRefusal(RuntimeError):
    def __init__(self, message, record):
        self.record = record
        super().__init__(message)


class LikelihoodUnsupported(NumericalRefusal):
    """Released likelihood table support failure, distinct from solver error."""


def point(values):
    if type(values) not in (list, tuple) or len(values) != len(COORDINATES):
        raise ValueError("exact seven ordered physical coordinates required")
    if any(type(v) not in (int, float) or not math.isfinite(v) for v in values):
        raise ValueError("finite binary64 physical coordinates required")
    return dict(zip(COORDINATES, map(float, values)))


def physical_support(values, contract):
    p = point(values)
    return all(contract["bounds"][name][0] <= p[name] <= contract["bounds"][name][1]
               for name in COORDINATES)


def class_parameters(values, contract, *, precision=None):
    """Parameter/unit mapping only; CLASS owns BBN and thermal evolution."""
    p = point(values)
    if not physical_support(values, contract):
        raise ValueError("predeclared physical prior exclusion")
    fixed = dict(contract["class_fixed"])
    if fixed.get("YHe") != "BBN" or "sBBN file" not in fixed:
        raise ValueError("explicit BBN-consistent CLASS table required")
    if any(name in fixed for name in ("omega_b", "omega_cdm", "H0", "A_s", "n_s", "tau_reio")):
        raise ValueError("varied cosmological coordinate supplied as fixed")
    fixed.update({name: p[name] for name in ("omega_b", "omega_cdm", "H0", "n_s", "tau_reio")})
    fixed["A_s"] = math.exp(p["logA"]) * 1e-10
    if "_resolved_bbn_path" in contract:
        fixed["sBBN file"] = contract["_resolved_bbn_path"]
    if "_resolved_class_source_root" in contract:
        fixed["hyrec_path"] = str(Path(contract["_resolved_class_source_root"]) / "external/HyRec2020") + "/"
        fixed["Galli_file"] = str(Path(contract["_resolved_class_source_root"]) / "external/heating/Galli_et_al_2013.dat")
    settings = contract["numerical_policies"][precision or contract["production_policy"]]
    if set(settings) & set(fixed):
        raise ValueError("numerical policy overwrites physical parameter")
    return {**fixed, **settings}


class ClassOwner:
    """Reuse the official compiled CLASS Python interface, not a physics copy."""
    def __init__(self, classy, contract):
        self.owner = classy.Class()
        self.contract = contract
        self.cached = None

    def evaluate(self, values, *, precision=None):
        started = time.monotonic()
        record = {"phase": "CLASS", "point": point(values), "policy":
                  precision or self.contract["production_policy"], "status": "started"}
        try:
            parameters = class_parameters(values, self.contract, precision=precision)
            key = tuple(values[:6]), record["policy"]
            if self.cached is not None and self.cached[0] == key:
                return {**self.cached[1], "cache_reused": True, "seconds": time.monotonic()-started}
            self.owner.set(parameters)
            if self.contract.get("physical_indicator") == "CLASS_Omega_Lambda_nonnegative":
                self.owner.compute(["background"])
                omega_lambda = self.owner.Omega_Lambda()
                if not math.isfinite(omega_lambda):
                    raise ValueError("nonfinite CLASS physical support predicate")
                if omega_lambda < 0:
                    return {"status": "physical_prior_excluded", "reason": "negative_Omega_Lambda",
                            "Omega_Lambda": omega_lambda, "seconds": time.monotonic()-started}
            self.owner.compute()
            raw = self.owner.lensed_cl(self.contract["lmax"])
            scale = (parameters["T_cmb"] * 1e6) ** 2
            spectra = {name.upper(): [float(x * scale) for x in raw[name]]
                       for name in ("tt", "ee", "bb", "te")}
            if (list(map(int, raw["ell"])) != list(range(self.contract["lmax"] + 1))
                    or any(len(row) != self.contract["lmax"] + 1 or row[:2] != [0.0, 0.0]
                           for row in spectra.values())):
                raise ValueError("exact CLASS ell0..lmax with zero monopole/dipole required")
            if any(not math.isfinite(v) for row in spectra.values() for v in row):
                raise ValueError("nonfinite CLASS spectra")
            derived = self.owner.get_current_derived_parameters(
                ["YHe", "z_reio", "100*theta_s", "Omega_m", "z_d", "Neff", "Omega_Lambda"])
            derived["H0"] = self.owner.h() * 100
            derived["r_drag_Mpc"] = self.owner.rs_drag()
            derived["omega_ncdm"] = self.owner.Omega_nu * self.owner.h() ** 2
            if any(not math.isfinite(v) for v in derived.values()):
                raise ValueError("finite CLASS derived state required")
            result = {"status": "completed", "spectra": spectra, "derived": derived,
                      "input_parameters": dict(self.owner.pars),
                      "seconds": time.monotonic() - started, "cache_reused": False}
            self.cached = key, result
            return result
        except Exception as exc:
            record.update(status="numerical_refused", error=str(exc)[:4096],
                          seconds=time.monotonic() - started)
            raise NumericalRefusal("CLASS refused inside admitted support", record) from exc
        finally:
            # This is official wrapper memory cleanup. Every admitted point gets
            # fresh CLASS state while the compiled library stays loaded.
            import sys
            active = sys.exception()
            failures = []
            for operation in (self.owner.struct_cleanup, self.owner.empty):
                try:
                    operation()
                except Exception as exc:
                    failures.append({"operation": operation.__name__, "error": str(exc)[:4096]})
            if failures:
                detail = {"phase": "CLASS-cleanup", "failures": failures}
                if isinstance(active, NumericalRefusal):
                    active.record["cleanup"] = detail
                elif active is None:
                    raise NumericalRefusal("CLASS cleanup refused", detail)


def guard_simall(spectra, calibration, support):
    """Mirror selected PLC lklbs.c calibration before its unsafe table index.

    Cl selection does Cl*window*unit*(1/(A*A)); window/unit are both1 in the
    admitted EE release. Keep its operation order and native float32 step.
    """
    scale = 1.0 / (calibration * calibration)
    ratios = []
    for ell in range(2, 30):
        selected = spectra["EE"][ell] * 1.0 * support["unit"] * scale
        dl = selected * ell * (ell + 1) / 2.0 / math.pi
        ratio = dl / support["stepEE_native_float32"]
        if not math.isfinite(ratio) or not 0 <= ratio < support["nstepsEE"]:
            raise LikelihoodUnsupported("SimAll table domain unsupported inside physical support",
                                   {"phase": "SimAll-support", "ell": ell,
                                    "calibration": calibration, "ratio": ratio if math.isfinite(ratio) else None})
        ratios.append(ratio)
    return {"status": "passed", "minimum_index": min(ratios), "maximum_index": max(ratios)}


class PrimaryOwner:
    """Retain official objects and report each raw released log-likelihood."""
    def __init__(self, likelihood, plc_root):
        self.transport = likelihood
        self.owner = likelihood.PlanckPrimary(plc_root, "plik_lite_TTTEEE")
        for name, axes in self.owner.contracts.items():
            if tuple(axes["extra_names"]) not in ((), ("A_planck",)):
                raise ValueError("unadmitted nuisance coordinate in " + name)

    def evaluate(self, spectra, calibration):
        components, rows = {}, []
        try:
            for name in self.owner.order:
                axes = self.owner.contracts[name]
                row = {"id": name, "status": "started"}
                rows.append(row)
                if name == "simall_EE":
                    row["support"] = guard_simall(spectra, calibration, axes["support_metadata"])
                vector = self.transport.build_clik_vector(spectra, {"A_planck": calibration},
                                                          axes["lmax"], axes["extra_names"])
                row["input_vector"] = self.transport.vector_identity(vector)
                returned = self.owner.objects[name](vector)
                if len(returned) != 1:
                    raise ValueError("exact scalar official likelihood return required")
                value = self.transport.finite_real(returned[0], name)
                row["raw_observation"] = self.transport.scalar_observation(value)
                if value <= -1e30:
                    raise ValueError("official invalid sentinel")
                components[name] = value
                row["status"] = "completed"
            return {"components": components, "loglike": math.fsum(components.values()),
                    "component_attempts": rows}
        except Exception as exc:
            kind = LikelihoodUnsupported if isinstance(exc, LikelihoodUnsupported) else NumericalRefusal
            raise kind("official primary refused inside admitted physical support",
                                   {"phase": "PLC", "components": components, "component_attempts": rows,
                                    "native_error": getattr(exc, "record", None), "error": str(exc)[:4096]}) from exc
