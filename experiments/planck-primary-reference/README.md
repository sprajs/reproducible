# Fully varied Planck primary reference

This new experiment asks whether a six-coordinate ΛCDM state plus the common
map-calibration nuisance can reproduce a source-matched released primary target.
It uses compiled CLASS and the official Commander TT, SimAll EE and Plik-lite
TTTEEE likelihoods. It includes no lensing-reconstruction likelihood and does
not qualify a native CMB replacement. The historical `lcdm-reference` and
conditional-H0 experiments retain their original source, parameter and SDK pins.

The new adapter maps physical `omega_b`, `omega_cdm`, `H0`,
`logA = ln(10^10 A_s)`, `n_s`, `tau_reio`, and `A_planck` to the admitted
compiled owners. BBN-consistent helium is computed by CLASS from an explicit
source-pinned BBN table; fixed-point helium is refused. Official objects remain
loaded between evaluations. The selected SimAll guard applies the source C
map-calibration scaling before its table-index check. Component values and
numerical refusals are retained separately from predeclared physical exclusions.

The physical/prior contract is now admitted from Prospector commit
`508b413bc05ce38148823923795898bb7ef073ec`,
`designs/candidate-class-planck-primary-six-parameter-v1.json`: 9,442 bytes,
SHA256 `2211b45de6876106557e30e0bb7ed1c696e165c5cb98c397f0a34c6e2b15e7d3`.
[candidate.json](candidate.json) preserves those exact bytes; [contract.json](contract.json)
accepts its complete consumer semantics. This is an explicitly chosen H0-flat
project target, with the source Gaussian calibration prior truncated to its
declared support. It does not reproduce the released CosmoMC angular-coordinate
measure or a Planck Table 2 posterior. The coupled nonnegative-Λ indicator uses
CLASS's full present massive-species density; its conditioning normalization is
not calculated, so evidence calculations remain blocked.

The new effective Fermi–Dirac realization fixes one 0.06 eV massive species,
`T_ncdm=0.71611`, degeneracy 1 and `N_ur=2.0327983725164924`, targeting nominal
Neff 3.046. It is distinct from the original adapter and the exact CAMB nonthermal
realization. CLASS owns varying BBN helium using the pinned 2017 table, HyRec and
the explicit reionization law. `hmcode_version=2016` is the source-supported
alias of CLASS's 2015 enum with the Mead 2016 neutrino additions. All three
released runtime nuisance tuples must be exactly `('A_planck',)`.

Run a bounded point attempt from a clean committed source, with the separately
admitted original-PLC and newly built CLASS Python-interface inventories:

```sh
python scripts/build_reference_classy.py --archive /absolute/class.tar.gz \
  --root "$PWD/.work/new-classy-runtime"
python experiments/planck-primary-reference/controller.py \
  --contract experiments/planck-primary-reference/contract.json \
  --runtime /absolute/primary-runtime.json \
  --classy-runtime "$PWD/.work/new-classy-runtime/runtime.json" \
  --attempt "$PWD/results/planck-primary-reference/fresh-attempt" \
  --points /absolute/ordered-points.json
```

The build requires an already installed isolated interpreter with NumPy, Cython
and setuptools; point scoring also requires SciPy. Each point supplies ordered
`values` and an optional named `policy`. The controller verifies candidate,
BBN, full source, executable/library and released-product identities before use
and again after returned failures. It retains binary64 theory bytes once per
new physical state/policy, referencing the same artifact for fast calibration
repeats. One retained numerical worker has an external watchdog; native hangs,
output overflow and physical/numerical/likelihood refusals remain distinct.
Per-file and captured log-prefix caps are hard limits; aggregate attempt usage
is monitored by polling. The parent terminal record survives a killed worker.

## 2026-10-09 executed controls and refusals

At Reproducible `c1a0e1af`, the explicit initialization control
`omega_b=.0223828, omega_cdm=.1201075, H0=67.32117, logA=3.044522437723423,
n_s=.9660499, tau=.05430842, A_planck=1` earned all three official initialization
selfchecks and two primary scores using freshly restored original inputs.
Default versus source `cl-permille` changed total log-likelihood by
−0.0899092251, within the declared 0.1 budget at this point only. CLASS took
11.34 and 11.64 seconds. Actual computed Neff was 3.04599659397, YHe
0.24540042595 and the full present massive physical density 0.00064420139037;
the nominal thermal mapping does not erase the visible quadrature difference.

The same attempt stopped at `logA=3.91, tau=.14, A_planck=.9`: Commander
returned its −1e30 refusal sentinel. A separate attempt at `75d4f3c3` preserved
the complete failed spectrum and reproduced the exact input-vector hash.
Independent source/FITS inspection identified calibrated TT Dl at ell 22,
2421.2311414262 µK², exceeding the released upper envelope 2343.0496262589 µK².
The witness follows the pinned Fortran's widened float32 π literal. This is a
likelihood-support failure, not a new physical-prior exclusion; v1 is not
qualified for posterior sampling. The earlier generic refusal is preserved.

At the same source, a proposed narrower-domain diagnostic with
`logA=3.4, n_s=.9, tau=.12, A_planck=.975` passed Commander but stopped before
SimAll compute: ell 4's table-index argument was 3110.1019089 versus the
required interval `[0,3000)`. No sentinel or unsupported point became −∞ or
a dropped chain step.

At `502f331c`, a second diagnostic tested four amplitude/slope/optical-depth
combinations at both calibration endpoints and six coupled density/H0 extremes
within `omega_b=[.018,.028], omega_cdm=[.08,.18], H0=[50,90], logA=[2.7,3.3],
n_s=[.92,1.05], tau=[.02,.10], A_planck=[.975,1.025]`. All 14 likelihood
evaluations completed. Calibration repeats reused four physical spectra; the
six spread solves took 9.77–13.49 seconds each. An additional v1 negative-Λ
control was correctly excluded by the predeclared physical indicator.
These selected tests do not qualify the whole proposed box, fix a new prior,
establish a posterior, or admit a DESI joint product. Numerical refinements,
complete support characterization, inference/convergence and a source-matched
comparison remain separate gates. No best fit or posterior has been produced.

The original input custody is `research-named-manifest/v1` at
`s3://research-data-436908790672-eu-west-2/reproducible/handoffs/reproducible/foundation-planck-primary-desi-original-inputs-20261009/versions/ffc90bd6f8bdd2e5bb85ca021a39b665a7fa83bfd28091962520f4b83172fad2/manifest.json`,
SHA256 `b3cb5a810216a036df5fa761ccf551646d392442d6070805cdac2bf264f5e7d0`,
VersionId `7Wx6k4nnXxL8qsgMuycTXK2qexElF8Tz`.

The complete selected engineering evidence, including failed and completed
attempts 001–010, both CLASSy build attempts, the exact compiled extension,
Commander witness, runtime inventories and the original CLASS reconstruction
archive, was published and freshly restored: 113/113 files, 30,569,337 bytes.
Its `research-named-manifest/v1` immutable manifest is
`s3://research-data-436908790672-eu-west-2/reproducible/handoffs/reproducible/foundation-primary-runtime-attempts-001-010-20261009/versions/f3775ed2ed48b79225e279c3c0de99a547beae7ef8562059743345a62460efd7/manifest.json`,
SHA256 `98410eea985b853355d0278ea9ea7611f95998be0ac6ab2035aad359b9a33bd6`,
VersionId `7LcdorQZoL7aXqlyG2lkeSz9IIOjitLV` (manifest 160,601 bytes).
The fresh restoration verified every selected byte identity. These custody
receipts establish recoverability of the runtime and complete refused prefixes;
they do not qualify a posterior or joint likelihood.
