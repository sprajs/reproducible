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

2026-10-08: clean source `fa7627fd94e182354e3200a247d8a307bf911711` completed
quick and broader profiles with the newly acquired source/runtime and full13
data. A separate fresh Git checkout rebuilt CLASS/PLC/SDK and independently
repeated quick; all fitted coordinates, χ² values, full scientific predictions
and separate official likelihood components matched exactly. Observed filesystem
paths, process timings and manifest hashes differ between independent attempts.

| Model | Quick H₀ | Quick χ² | Broader H₀ | Broader χ² | Separate broader Planck raw log likelihood |
| --- | ---: | ---: | ---: | ---: | ---: |
| Flat ΛCDM | 68.833139 | 10.641052 | 68.831349 | 10.641026 | −626.154767 |
| Flat w = −0.9 | 66.698450 | 16.957094 | 66.697421 | 16.957078 | −866.973292 |

H₀ units are km s⁻¹ Mpc⁻¹. Quick used 23 evaluated points per model and a
0.03768749 final bracket; broader used 46 and 0.00621124. The H₀ changes are
−0.001790 and −0.001030, with χ² decreases of 0.00002584 and 0.00001603.
These are empirical optimizer-resolution comparisons, not confidence intervals
or certified CLASS accuracy. Both models' full-output final states gave exactly
the same DESI χ² as their faster fit states. Every inferred dark-energy density
was positive. All three official test vectors passed the unchanged 1e−6 gate;
the fixed A_planck relative prior penalty is zero and remains separately declared.
Full requests had no unused controls; fast requests left only the five deliberately
unused output selectors. Later guards explicitly admit this consumption policy
and force parent-process OMP/BLAS threads to one before loading the C API.

Primary quick completed in 98.82 s, retaining 1,059,968,127 B in 719 files.
Broader completed in 128.01 s, retaining 2,053,894,930 B in 1363 files, within
the unchanged 2 GiB attempt ceiling. Their manifest hashes are
`f8853aa49ac9680b823ae5e9ae0bda266caf20b0486e293d2e48982f7db66042` and
`4a33be8b84a9d44d8c080eae5863436b26b3029fe0d5b429a3c883613da3d02d`;
the independent fresh quick manifest is
`4b4a93fc0ac6915213a3881a2b95bb373a976f9f35f57fc34094da32c5608f68`.
Plots retain signed TE, separate linear/Halofit spectra, and covariance-aware
fit scores; residual marginal-error scaling is explicitly for display only.
No joint CMB/BAO score, posterior, calibrated SN fit or native CMB qualification
is inferred. The separate raw Planck values are conditional evaluations at each
DESI minimum, rather than CMB-fit optima or a combined model-evidence statistic.

The first primary and fresh attempts at `a924cf98` retained the same explicit
CLASS input failure: even `non linear = none` is rejected when perturbations are
not requested. A new source/attempt omitted that selector to use the pinned
source default; the original refusals and successful official test vectors are
preserved locally. Source `a92bccea00b95e3afb1f91582304567141b6cf59` then completed
quick with explicit consumption admission and recorded parent thread settings
all equal to one: 57.03 s, 767 files, manifest
`ec51ebf2682c7288376e6cabd0d6e64986656a0f7180905d14b8eb12ee718385`.
Its fitted values and separate Planck components matched the preceding quick
runs exactly. The final source additionally restores the original selected-CLDF
directory-tree gate; that structural gate and retained-product likelihood replay
have separate receipts rather than rewriting any of these attempts. Durable
archive status remains separate; no upload is implied by local records.
