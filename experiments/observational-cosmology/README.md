# Observational conditional cosmology fit

This dedicated experiment fits H₀ to the exact released DESI DR2 full13 Gaussian
BAO compression, first with flat ΛCDM and then with flat constant w = −0.9.
It uses pinned CLASS v3.3.0 for backgrounds, its predicted drag ruler, lensed CMB
and linear/Halofit matter power, and the existing compiled Irreducible Gaussian
consumer for every score. No solver or Gaussian density is rebuilt in Python.
[design.json](design.json) declares the complete bounded question and limits.

The base state comes from the existing [CLASS reference](../lcdm-reference/README.md),
whose supplied point is conditioned on a Planck primary-plus-lensing source
result. Only H₀ varies; physical baryon/CDM densities, thermal species, primordial
state, fixed helium and reionization stay explicit. The alternative selects the
constant-w subclass of CPL, with w₀ = −0.9, wₐ = 0, unit fluid sound speed and
explicit PPF policy. It sets Lambda and scalar-field densities to zero and
**omits** the inherited fluid-density entry, allowing CLASS to infer its density
from flat closure. It is a chosen supported alternative, not the paper best fit.

The exact ordered 13-row means and full 13×13 covariance are acquired together
from the pinned public release. Both quick and broader profiles keep all rows,
including the final DH/DM ordering and every covariance entry. The selection
helper retains a common ordered principal submatrix on both axes; this native
consumer deliberately supports only the full13 selection. These data are fitted
distance summaries with reconstruction/fiducial calibration, not raw galaxies.

From a fresh checkout, install Python 3.11+, `uv`, a C/C++ compiler, Fortran,
BLAS/LAPACK development libraries and standard build tools. Runtime bootstrap
details and concrete platform requirements are documented by its help output.
Use one local build/job, with OMP/BLAS set to one:

```sh
uv sync --frozen
python -B scripts/bootstrap_cosmology.py --root "$PWD/.work/cosmology-runtime"
python -B experiments/observational-cosmology/acquire.py --root "$PWD"
python -B experiments/observational-cosmology/controller.py \
  --runtime "$PWD/.work/cosmology-runtime/runtime.json" \
  --attempt "$PWD/results/observational-cosmology/quick-001" \
  --profile quick --planck \
  --deadline-utc "$(date -u -d '+60 minutes' +%Y-%m-%dT%H:%M:%S+00:00)"
uv venv .work/plots
uv pip install --python .work/plots/bin/python --require-hashes --only-binary=:all: -r requirements/plots.txt
.work/plots/bin/python experiments/observational-cosmology/plot.py results/observational-cosmology/quick-001
```

Each attempt directory must be new. The bootstrap writes pinned source, actual
build and executable inventories; acquisition refuses changed bytes. The
controller requires clean committed Reproducible source and preserves raw CLASS
products, input requests, native Gaussian outputs, failed prefixes and a terminal
manifest. It checks source/runtime/data identities before and after the run.
The manifest hashes the complete retained inventory except itself, and records
the finite fit resolution, observations, calibration and gate distinctions.
Plotting checks saved product hashes and writes its own figure/environment
manifest. Generated products and third-party inputs remain ignored local storage.

Quick uses nine evenly spaced H₀ points between 55 and 85 km s⁻¹ Mpc⁻¹, brackets
the best interior grid point, then performs at most twenty deterministic
golden-section refinements to a 0.05-wide bracket. Broader uses 31 grid points
and a 0.01 bracket, with at most 28 refinements. A boundary optimum is refused;
neither profile silently expands the model domain. To run the broader profile,
change `--profile broader` and use a new attempt path. The optimizer reports the
best actually evaluated point, not an unevaluated polynomial estimate, and no
posterior or uncertainty interval is inferred from its numerical bracket.

`--planck` scores the DESI-conditional best points using official Commander TT,
SimAll EE and Plik-lite TTTEEE, with A_planck fixed to one and its relative prior
penalty separately declared. Plik-lite's released foreground marginalization
and fixed calibration remain part of that target. Official test vectors must
pass the unchanged 1e−6 printed-difference gate. These CMB scores are separate;
the workflow has no joint-probe likelihood. Omitting `--planck` requests the
DESI fit and predictions alone. No SN target is acquired or fit here; the
[original refusal and symmetric working profile](../sn-symmetric-working-profile/README.md)
retain their own identities and limitations.

All production physical predictions come from CLASS; native Irreducible physics
qualification remains a separate programme. The final full-output state is
rescored against DESI and its difference from the faster background-only fit
policy is retained. Printed tables, six-decimal ruler output and background
interpolation have no certified aggregate error bound here. Unit-test recovery
and covariance controls are synthetic and never enter the observational score.

Exact full evidence needs a durable archive. The optional
[archive workflow](../../docs/archive.md) uploads only explicitly selected,
lawfully redistributable evidence using runtime credentials and pinned object
versions. Public downloads should normally retain their immutable acquisition
route rather than being redistributed. No cloud credential or storage binding
is committed in this packet.

## Findings

2026-10-08: controller and fresh-runtime recipe under integration. An observational
result is pending the committed real-data run and independent fresh-checkout
review. Existing fixed-point reference scores are not being relabelled as fits.
