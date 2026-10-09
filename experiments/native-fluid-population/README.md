# Native fluid and collisionless population responses

This new compiled SDK campaign compares supplied generalized Chaplygin backgrounds
and self-gravitating isotropic Plummer populations. These distinct synthetic
models supply no observed fit, likelihood, prior or posterior. Previous six-model
results and pins remain unchanged. [request.json](request.json) freezes grids,
units, native identities, empirical comparison budgets and resource limits.
Final production SDK/source pins require root's completed integration; the early
SDK is API-compile-only. The generic packet stays blocked because its runner has
no registered route for this dedicated controller.

Python only admits inputs, controls processes, compares retained outputs and
plots. Physical predictions are actual installed Irreducible calls. Unchanged
[admission helpers](../native-model-campaign/controller.py) are snapshotted; all
installed files and manifest scientific hashes are checked before/after execution.
Run from a clean committed checkout:

```sh
python -B experiments/native-fluid-population/controller.py \
  --sdk /absolute/final-sdk --engine-source /absolute/clean-science-pin \
  --build-manifest /absolute/build-manifest-release.json \
  --attempt "$PWD/results/native-fluid-population/UNIQUE" --profile quick
```

Fresh attempts allow one compiler job/thread, 300 seconds/process, 512 MiB address
space and 32 MiB evidence. Compiler/library/consumer identities and failures,
refusals, source drift and timeouts are retained. Plots verify native byte hashes.

Chaplygin uses flat GR with separately conserved ordinary dust (.3), no radiation
in this sweep and remaining .7 barotropic fluid. Supplied A_s=[0,.3,.7,1] and
alpha=[0,.5,1] produce background E/H, density, fractions, equation of state,
formal dp/de, deceleration and flat distances. Nonincreasing quick a=[1,.5,.2,.1,.05]
lies within the native [1e-4,1] domain; future a=2 is a deliberately refused
control. Formal dp/de supplies no qualified propagation/perturbation law,
including at vacuum. Distinct compiled FLRW endpoint controls use
Omega_m=.3+.7(1-A_s), Omega_Lambda=.7 A_s for alpha=0 and A_s=0/1; arbitrary
alpha is never replaced by GR dust plus Lambda.

Plummer supplies M=[1e40,1e41] kg, b=[1e19,3e19] m and nominal
G=6.67430e-11 SI. This is Newtonian isotropic collisionless equilibrium with mass
tracing tracer, not a collisional gas, relativistic model or independently
calibrated tracer. Prepared native rho, relative potential, mass, projected
density, escape speed, one-axis variance and density-weighted LOS variance are
retained. f(E), local vector-velocity PDF and speed PDF have distinct units.
Speed inputs are explicit q times native escape-speed output.

Quick r/b=[0,.1,.5,1,2,5,10], q=[0,.25,.5,.75,.9,1,1.001] retain every row.
q=1 is a support-boundary diagnostic with velocity comparison unassessed; native
status, energy and inherited empirical error are retained. Its separate contract
gate requires positive-energy admitted fields, outside exact zero or ambiguous
conditioning refusal consistent with the native diagnostic interval. q=1.001 is
an outside control only when native support says outside, energy plus its
empirical diagnostic is nonpositive and all three outputs are admitted exact
zero. This is no certified support enclosure. Negative speeds are refused.

Frozen final relative allowance is 2e-6; equations of state/formal slope use
absolute 1e-8; distances additionally receive 1e-4 Mpc; exact zeros use 1e-12.
Tighter Chaplygin policy refines adaptive quadrature; tighter population policy
only changes admission budgets on unchanged closed-form arithmetic, not
precision. Passing means finite admitted-grid agreement with retained boundary
diagnostics, never certified global accuracy or qualified observations. Broader
adds coordinate sampling with the same parameter states. Permanent engine
independent density/velocity integrals, moments, Jeans checks and fixtures are
separate pinned reference evidence, not inferred from policy comparison.

Full completed/failed/partial records, configs/source snapshots, identities and
plots use named S3, exact-version readback, manifest-last and fresh restoration.
Raw papers/rights-unverified excerpts are excluded. Actual findings and archive
pins follow after execution; final merge also requires the engine dependency's
merge and exact-main CI.

2026-10-09: final scientific source 9f51b53, with exact SDK/build/library pins in
request.json, produced quick-002 (32 cases/512 rows, 1,540 admitted comparisons)
and broader-001 (32/1,608, 4,088). Both had zero comparison failures and passed
all 11 compiled endpoint/refusal controls. All 56/112 q=1 native rows were
ambiguous conditioning refusals with consistent empirical energy diagnostics;
accuracy there remains unassessed. Tightening budgets changed no physical
assumptions. Original quick-001 passed native execution and qualification but
its Python caller exited 1 because an empty failure list was passed to
SystemExit. That original/source and call observation remain immutable; the
integer-exit correction was rerun into fresh attempts. Provisional SDK use was
strict API compilation only, with no physical execution.

At A_s=.7,a=.1, native E is 22.5940 for alpha=0 versus 26.1420 for alpha=1;
these distinct backgrounds were not replaced with dust plus Lambda. Population
plots retain compact non-Gaussian speed profiles and withheld boundary values.

All 68 selected files (10,072,916 bytes), including the caller failure, were
published and freshly restored byte-identically:
`s3://research-data-436908790672-eu-west-2/reproducible/experiments/native-fluid-population/attempts/20261009t032441z-51fcfc5ec757/versions/6072deea7003a53d2f1c7b8cb3fd419c98b20aa313da9e69759e0c44469665f7/manifest.json`,
SHA256 `51ac32c39d4bee3474067dc6a0563fdbbe68b69c4c2aabdeb08921272523bf12`,
VersionId `O4MiKsebFLFqXr0_IxeAHoZ1g8DSNCKj`, `research-named-manifest/v1`.
Both PNGs replayed byte-identically from restored source/native JSON; original
SVGs also restored exactly. This recovery adds no numerical certification.
Locals are retained. Engine PR69 merged e58fcd5 with exact-main CI success.
