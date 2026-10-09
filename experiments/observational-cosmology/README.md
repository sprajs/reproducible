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

The executed build baseline is **Debian 13 x86_64, Linux ELF with glibc and
`ldd`**. The bootstrap requires Python 3.11+ available as `python`, `uv`, GNU
`make`, CMake ≥3.24, C and C++20 compilers available as `cc`/`c++`, and the
`ld`/`ar` binutils. The official PLC build also needs a Fortran compiler and
CFITSIO development headers, plus BLAS/LAPACK, CFITSIO and Fortran runtimes.
Its linker resolves these exact
runtime SONAMEs through `cc -print-file-name`: `liblapack.so.3`, `libblas.so.3`,
`libcfitsio.so.10` and `libgfortran.so.5`; `ldd` must resolve every resulting
shared dependency.

On Debian 13, install the system prerequisites before running the recipe:

```sh
sudo apt-get update
sudo apt-get install build-essential cmake gfortran libblas-dev liblapack-dev \
  libcfitsio-dev libc-bin python3 python3-venv python-is-python3 ca-certificates
```

These development packages pull in the runtime libraries, including Debian 13's
`libcfitsio10t64` package providing `libcfitsio.so.10`. Install `uv` using its
[installation instructions](https://docs.astral.sh/uv/getting-started/installation/).
An existing compatible CMake outside `PATH` can be selected with
`--cmake /absolute/path/to/cmake` on the bootstrap command.

The script has a pinned **Debian 13 x86_64-only** fallback when the Fortran
compiler or `/usr/include/fitsio.h` is missing: it uses `dpkg-deb` to extract
the compiler/development headers into the ignored runtime's `tools/` directory.
Required runtime SONAMEs and the other build tools must already be available.
This Linux/glibc recipe needs a separately reviewed build route for macOS or
other libc/architecture combinations; the recorded execution remains the named
Debian baseline.

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
The optional `--input-root /absolute/restored-root` selects a separate working
root containing both exact files at their declared `data/bao/` paths. It checks
the same release byte lengths, SHA256 hashes, ordered full13 means and covariance
before and after the attempt. It acquires no inputs; missing, changed or linked
inputs are refused. The default remains this checkout. Record the selected exact
S3 manifest URI/SHA256/VersionId and authoritative restore route in preservation
provenance; a local working root is not that immutable source identity.

```sh
python -B experiments/observational-cosmology/controller.py \
  --runtime "$PWD/.work/cosmology-runtime/runtime.json" \
  --input-root "$PWD/data/restored-desi-root" \
  --attempt "$PWD/results/observational-cosmology/restored-quick-001" \
  --profile quick \
  --deadline-utc "$(date -u -d '+60 minutes' +%Y-%m-%dT%H:%M:%S+00:00)"
```

Use a new attempt name for every invocation. A restored dataset must match the
declared directory layout; follow its catalog restore route rather than treating
an acquisition recipe or preservation bundle as a named directory manifest.
The command above omits the separately optional Planck score.

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

2026-10-09: PR25 clean source `52aa10f6` passed its actual separate-input-root
acceptance after exact-version historical S3 restoration of both full13 files;
the catalog's named DESI entry itself remains acquisition-only. A fresh serial
CLASS/PLC/SDK build preserved original scientific pins and recorded actual new
executable hashes. S3 quick and independent upstream-acquired quick matched
scientific values exactly. Optional broader retained the same data and changed
only optimizer resolution. Actual quick H0/chi2 are 68.8331390311/10.6410517554
(LCDM) and 66.6984504953/16.9570944841 (fixed-w PPF); broader values are
68.8313494551/10.6410259197 and 66.6974207976/16.9570784500. Official vectors passed
1e-6, full-output score differences were zero and both quick plots were inspected.

The separately predeclared 14-case numerical sensitivity attempt is execution-
complete but **rejected/incomplete**: fixed-w H0=75 source-supplied precision
changes separate Planck logL by+0.29961458, exceeding its 0.2 budget; integration
refinement has no exact common printed matter-k axes for the declared Pk check.
Those failures remain distinct from the successful consumer and optimizer gates.
No tolerance was weakened, posterior/joint score inferred or aggregate numerical
bound certified. The [attached-runtime account](../../docs/s3-workflow-validation-2026-10-09.md#attached-runtime-validation-2026-10-09-utc)
records exact builds, profiles, sensitivity settings and archive/recovery pins.
