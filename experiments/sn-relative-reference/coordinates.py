"""A proposal coordinate change; the declared physical box remains the prior."""
import math

PHYSICAL = ("omega_b", "omega_cdm", "H0", "M")
TRANSFORMED = ("omega_b", "Omega_cb", "eta", "calM")
BOUNDS = ((0.018, 0.028), (0.08, 0.18), (50.0, 90.0), (-21.0, -17.0))
LOG_PRIOR = -math.log(math.prod(hi - lo for lo, hi in BOUNDS))
ETA_BOUNDS = (math.log(0.5), math.log(0.9))


def forward(physical):
    if len(physical) != 4 or not all(math.isfinite(x) for x in physical):
        raise ValueError("finite four-coordinate physical vector required")
    wb, wc, H0, M = physical
    if H0 <= 0:
        raise ValueError("positive physical H0 required")
    h = H0 / 100.0
    eta = math.log(h)
    return (wb, (wb + wc) / h**2, eta, M - 5.0 * eta / math.log(10.0))


def inverse(transformed):
    """Return an admitted physical vector, or a physical-prior exclusion.

    No clipping, rectangular transformed prior, or numerical-refusal conversion.
    Membership uses the actual binary64 inverse values and the unchanged closed
    physical bounds. Exact endpoint roundtrips can differ by one rounding bit;
    no tolerance enlarges the physical support.
    """
    if len(transformed) != 4 or not all(math.isfinite(x) for x in transformed):
        raise ValueError("finite four-coordinate proposal required")
    wb, Omega_cb, eta, calM = transformed
    if not ETA_BOUNDS[0] <= eta <= ETA_BOUNDS[1]:
        return None
    h = math.exp(eta)
    physical = (wb, h**2 * Omega_cb - wb, 100.0 * h,
                calM + 5.0 * eta / math.log(10.0))
    if not all(lo <= x <= hi for x, (lo, hi) in zip(physical, BOUNDS)):
        return None
    return physical


def log_jacobian(transformed):
    """log |d(wb,wc,H0,M)/d(wb,Omega_cb,eta,calM)| = log100+3eta."""
    return math.log(100.0) + 3.0 * transformed[2]


def uniform_control_target(transformed):
    physical = inverse(transformed)
    if physical is None:
        return -math.inf
    return LOG_PRIOR + log_jacobian(transformed)
