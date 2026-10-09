# Reproducible roadmap

This is the sole active experiment, data, inference and evidence plan, reset on
2026-10-09 against `bc5de0da41e8136dfe9b4852f3a792692d556e73`. The user's current
programme direction supersedes older operative priority paragraphs; Git at that
revision retains their history. [Current gaps](gaps.md) records evidence and
limits, not a second work queue. Historical requests, models, source snapshots,
SDK/build pins, failures, covariance refusals and archive identities remain intact.

The coordinated programme uses the same milestone IDs in
[Prospector](https://github.com/sprajs/prospector/blob/main/docs/roadmap.md) and
[Irreducible](https://github.com/sprajs/irreducible/blob/main/docs/roadmap.md).
Prospector owns sourced claims and candidate design; Irreducible owns production
physical/numerical models and interfaces; Reproducible owns dataset admission,
likelihood composition, fitting, diagnostics, plots and immutable attempt records.
A conventional working ΛCDM reference establishes a comparison, not cosmological
truth. Engine completion, numerical quality, source validity, inference,
observational applicability and interpretation have separate acceptance gates.

## M0 — Freeze the actual reference and data contracts

The first work package is a new immutable source-defined reference design, not
a repin of `lcdm-baseline` or a promotion of the conditional H0 experiment.
Reproducible accepts Prospector's exact likelihood/source contract and records:

- The named released primary-CMB target and version, spectra/multipoles, masks,
  beam/foreground/calibration nuisance treatment, likelihood normalization and
  cosmological/calibration priors. Commander + SimAll + Plik-lite primary is a
  distinct target from full Plik plus reconstruction in a Planck Table 2 column.
  Use only the result benchmark whose components and priors actually match.
- All six cosmological coordinates and their parameterization: physical baryon
  and cold-dark-matter densities, primordial amplitude/slope and pivot,
  reionization optical depth and expansion/angular-scale coordinate; transformations,
  bounds and measure are explicit. Pin neutrino species/masses/distributions,
  geometry/gravity, recombination/reionization and helium/BBN policy. A fixed
  source-point YHe does not supply a BBN-consistent relation as omega_b varies.
- Exact free/fixed nuisance coordinates and sourced priors; the illustrative
  CLASS point remains an initialization/reference, never an extra independent
  measurement or a prior derived from the likelihood being fitted.
- Dataset release, raw/calibrated/reduced/fitted/synthetic role, ordered rows and
  axes, units/frames, masks, selection, calibration, covariance/shared-object
  ancestry, source hashes and copying rights. A posterior summary is a fitted
  product; DESI distances are model-conditioned BAO compression, not raw galaxies.

Use the already verified storage-startup discovery and its immutable catalog
pin. Resolve only selected named resources, inspect their authoritative format
and routes, and distinguish acquisition declarations from verified payload.
Inventory primary CMB, BAO, SN/ladder, clustering, lensing, thermal/abundance and
instrument/template families, including absent or unassessed lower-level inputs.
Restore/acquire the selected baseline into a fresh ignored directory; exact
length/hash/version checks and source semantics precede use. Shared resource
metadata and historical local existence do not establish current payload custody.

Acceptance: reviewed candidate/design plus exact data/likelihood/prior/dependence
ledger, explicit admitted versus blocked components, lawful reconstruction route,
actual runtime/source/build/executable inventories and a bounded resource budget.
All source identities must survive before/after admission. M0 source work for
broader probes proceeds alongside the baseline rather than inflating its first fit.

## M1 — Reproduce a fully varied released ΛCDM reference

Use existing pinned CLASS and official likelihood tools to execute the accepted
M0 target. Native full CMB replacement is a separate M3 dependency and does not
block this external reference. Python orchestrates existing solvers and likelihoods;
new shared physics remains in Irreducible. A small experiment-specific controller
is the first implementation; add reusable infrastructure only for a real consumer.

First freeze a numerical policy over the chosen ΛCDM fit domain. Compare independent
background/thermal/hierarchy/projection/table/interpolation refinements at representative
and boundary parameter points, with per-observable and final likelihood budgets.
Printed drag precision and resampling need explicit downstream score allocations.
Retain the prior fixed-w H0=75 failure (+0.29961458 Planck logL versus 0.2) and the
unearned full-grid matter-P(k) comparison. That excluded extension's failure does
not automatically block a qualified ΛCDM domain; any later extension closes its
own gate. Never weaken the historical budget or claim an optimizer bracket is a
solver error certificate.

The existing theory adapter only admits the anchor and ns ± 0.005, and the
first official likelihood adapter requires fixed A_planck=1 and Plik-lite. Create
a separately reviewed six-coordinate/calibration-nuisance adapter and consumer
identity; preserve those historical routes, hashes and restrictions unchanged.
Then implement a bounded multi-coordinate optimizer and posterior sampler for
all sourced cosmological/nuisance axes, with explicit priors, transformations,
seeds, starts, adaptation, checkpoint and termination policies. Preserve failed,
out-of-domain, numerical-refused and interrupted evaluations. A numerical/solver
refusal inside the admitted physical prior domain must not become logL = −∞,
a dropped chain step or a silent support cut. Stop and repair the numerical
policy, or explicitly declare a new prior/domain identity and requalify it,
preserving the failed prefix. Predeclared physical prior exclusions are distinct.
Freeze requirements
before execution: multiple separated chain starts, mixing diagnostics, Rhat,
effective sample size, Monte Carlo error, tail/support checks, and a matching
released likelihood/posterior benchmark at stated statistical/numerical accuracy.
Posterior normalization is needed only for statistics that require it; a sampler
still needs the declared probability measure and convergence evidence.

Acceptance: a clean new source/build/request identity, successful numerical
qualification across the admitted domain, a fully varied reference posterior,
per-component likelihood/prior records, explicit convergence evidence, matched
source reproduction comparison, covariance-aware residuals and inspected plots.
Publish the selected full evidence and original failures to named S3, then restore
into a fresh directory and replay saved scores/plots by their byte identities.
This gate earns only the named released target; no omitted lensing likelihood,
full-Plik nuisance target or native CMB qualification is inferred.

## M2 — Fit a first defensible joint reference target

While M1 runs, Prospector and Reproducible qualify DESI compression applicability
and the faithful SN residual/covariance/source semantics. Preserve the original
Pantheon+ nonsymmetric-matrix refusal and separately named symmetric working
profile. Resolve calibration/selection/duplicate/calibrator dependence and the
ladder's unresolved axes/joins before claiming their observational contribution.
Do not reconstruct physical H0 systematics from synthetic constraint-mean shifts.

Build an explicit pairwise shared-object/calibration/estimator map: primary versus
lensing/ACT CMB; BOSS P nested in P+B and shared-galaxy BAO/DESI products;
Pantheon+/SH0ES/SALT/Fragilistic overlap. Admit a joint composition only when each
factor's applicability, common parameter/nuisance/prior ownership and dependence
are justified. Source-supported negligible-dependence approximations may be
accepted with sensitivity evidence; unknown material dependence blocks the
affected combination. Keep independently qualified probe fits available when a
joint component remains blocked.

Acceptance after M0/M1: one explicitly named qualified joint subset, simultaneous
parameter/nuisance inference and convergence, per-probe contributions and residuals,
parameter shifts with the relevant covariance, posterior predictive diagnostics,
held-out/selection checks and calibrated tension statistics. Predeclare predictive
and tension measures and their simulation/coverage policy. A difference between
conditional H0 minima is not a tension significance. Publish chains, covariance,
predictive draws, diagnostic/plot source and failures with exact restore pins;
verify retrieval in a fresh runtime.

## M3 — Compare native physical closures and public interfaces

Reproducible supplies bounded comparison consumers for Irreducible's sourced
thermal/recombination/late-opacity/drag, perturbation/species/transfer/amplitude,
primary projection/polarization/lensing and geometry work. Map exact physical
states, units, observable axes and numerical budgets to the qualified external
reference. Supply independent method references, analytic limits and separate
refinement axes; identical corpus outputs do not create a new accuracy bound.

Acceptance: only supported shared observables are compared at matched source
states and actual SDK/build identities; model/numerical/refusal boundaries remain
visible. Native massless/supplied-drag, thermal supplied-drag and full CLASS states
retain distinct IDs and scopes. A narrower native consumer does not replace the
released M1 target. M3 can proceed in parallel with M1/M2 using coordinated jobs.

## M4 — Complete one real lower-level vertical and broaden data coverage

Start source-led work now; execute a vertical only after its contract closes.
Prioritize one mass + light + stellar-kinematics lens system alongside an identified
SN/instrument or clustering target, choosing the smallest observationally
identifiable consumer. Acquire raw observations and approved reductions separately,
with original reduction provenance, calibration, selection, covariance and rights.

For SN, map physical event/frame/clock/exposure/units and extraction ancestry;
resolve SALT spectral-time/training/error/extinction and Fragilistic calibration
index/generator laws; retain signed fluxes and nondetections. A sourced population,
source evolution and survey selection law is required beyond expansion and optical
kernels. For clustering, admit catalog/randoms, masks/windows, reconstruction,
AP/fiducial maps, bias/nonlinear/scale cuts, mocks and estimator covariance before
using RSD/fullshape or reusing BAO under unusual theories. For lensing, admit
image/delay/PSF/light/kinematic/aperture/environment/selection likelihoods and mass-sheet
or anisotropy uncertainty; isolated halo models remain prerequisites. Adding NFW
or Hernquist to a self-gravitating Plummer potential invalidates the existing
population DF and requires a new common-potential tracer/DF/Jeans owner.

Maintain explicit coverage for BBN abundance observations, weak lensing/cosmic
shear, standard sirens, chronometers, cluster counts, Lyα forest and
21cm/line-intensity probes.
These future disciplines start with source/data/likelihood contracts, not invented
availability. Acceptance: one source-to-prediction-to-likelihood vertical with
measured calibration/selection and predictive validation, plus a factual breadth
ledger that distinguishes present inputs, acquisition plans and unassessed assets.

## M5 — Discriminate compatible candidates and combinations

After M1 and each required probe's qualification, accept Prospector's immutable
candidate equations, source domains, changed parameters, priors, identifiability,
conservation/stability and data-applicability contracts. Fit the same admitted
reference subset at matched numerical quality and common nuisance treatment;
extra physics belongs in Irreducible. Retain posterior/predictive comparisons,
parameter sensitivity and any evidence/normalization/prior-volume policy.

Source work can run earlier for conventional comparisons, EDE versus NEDE,
conservation-qualified decay/daughter-scalar, Chaplygin perturbation choices and
directional Bianchi/timescape candidates. Retain exponential slope-variance
obstructions, Gauss–Bonnet action/stability failures and DGP's self-accelerating
ghost caveat. Ten finite native models provide no complete CMB/LSS inference.
A combination needs one action/conservation/initial-state/parameter owner; no
independently normalized H(z) addition, double-counted energy or unqualified
vanilla nonlinear prescription. List incompatible and unresolved combinations.

Acceptance: at least one compatible candidate compared with the frozen reference
using complete likelihood/parameter/numerical identities, adequate inference and
predictive diagnostics, genuine data applicability and immutable recoverable
results. Rejected candidates and failed controls remain part of the account.

## M6 — Make cloud execution fast and recoverable at fixed quality

Apply this milestone to every meaningful attempt. Start with prepared-tool
activation when supplied by the environment, current bounded storage discovery,
selected exact manifests and a clean input directory. Preserve credentials,
profiles, proxy and TLS trust. Cloud's restricted identity writes under
`reproducible/`; shared catalog and engine-evidence curation use the separately
authorized identity. No bucket-root discovery is needed.

Default to one compiler/process job and one OMP/BLAS thread; root coordinates the
shared ceiling of four local jobs across all repos. Record deadlines, memory,
evaluation quotas, file/transfer bounds, actual CPU/wall time and numerical
policy. Benchmark identical admitted scientific inputs before optimization;
measure subprocess, preparation, source/file-hash and storage-readback costs.
The existing observational controller starts CLASS and Gaussian subprocesses
per evaluation; covariance preparation is reused inside each process, not across
the full fit. A new retained-factor/batched consumer needs its own reviewed
identity. Cache invariant preparation by complete input/model/build identity and retain
refused outputs. Improve coarse batch boundaries only when a real workload shows
benefit; performance changes must preserve the accepted quality and diagnostics.

Save complete, failed, interrupted or honestly selected reconstructable attempts
under named experiment/handoff collections. Record URI/SHA256/VersionId/format,
per-file roles/rights, source/candidate/request/input/executable identities,
seeds/policies and omission/regeneration ancestry. Byte-check each exact remote
version before publishing the completion manifest. Fresh restoration and score/
plot replay precede custody claims; upload and CI do not confer science quality.
Useful bulk state belongs in S3, with concise findings/source in Git. Never delete
the only copy or silently change old SDK/receipt/model pins.

Acceptance: measured end-to-end speed at the same scientific gates, cold-runtime
reconstruction and retrieval evidence, recoverable progress/failures and an
explicit report of blocked uploads or unpreserved work.

## Execution order and review

M0 and M1 are the immediate scientific path. M0 probe/source work, M3 closures,
M4 lower-level contracts and M5 source screening can proceed independently;
M2 and cosmological M5 claims depend on M1 plus their applicable source/numerical
contracts. M6 and explicit immutable evidence apply throughout. Each work package
has one owner, a bounded question and a reviewable acceptance record; superseded
queues do not reopen completed requests. Use the normal PR/review/check workflow
and exact-head CI for implementation, preserving unrelated active worktrees.
