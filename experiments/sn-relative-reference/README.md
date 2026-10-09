# Relative Pantheon+ background reference

This new working target uses the producer-relative selection `zHD > 0.01`:
1,590 original occurrences, including ten calibrator-flagged rows. Every selected
row has the cosmological mean
`5 log10[(1+zHD)(1+zHEL) DA(zHD)/Mpc] + 25 + M`, compared with `m_b_corr`.
The flags do not introduce a Cepheid mean in this relative factor. The exact
[Prospector source snapshot](candidate.json) is revision
`2a7b21cb7f93983434f1cea9bd707ea2547044a2`; its original contract path is
`register/contracts/foundation-relative-and-calibrated-sn-working-v1.json`,
SHA256 `8430dc7a5e916ca4a685dd6d141d37eb3eed4c870f830d26cd2cc5db61f15858`.

The original selected STAT+SYS principal covariance is exactly symmetric and
positive definite. Its 20,224,800-byte row-major big-endian binary64 identity is
`5edd58efb7a29825a29246a29c90e3d95ddcabe9cf7cdb063b271824f221c66e`.
The half-sum artifact has identical bytes, so this target needs no covariance
repair. The original full 1,701-row and calibrated 1,657-row asymmetry refusals
remain separate. A failed relative attempt inherited an assumption of positive
asymmetry; its prefix is retained. A later append-only correction fixes a mistaken
receipt label and records four signed-zero-only serialization differences in
triangle controls. Those triangle files are not the consumer covariance.

[The contract](contract.json) fixes the probability measure and precision policy.
The normalized Gaussian contains the complete selected covariance once; no
Cepheid, independent H0, extra calibration or CMB factor is added. Proper uniform
priors are `omega_b ∈ [0.018,0.028]`, `omega_cdm ∈ [0.08,0.18]`,
`H0 ∈ [50,90] km/s/Mpc` and `M ∈ [-21,-17] mag`. Spectral/reionization coordinates
are conditioned at the declared anchor; flat GR, fixed photon/relic species,
BBN and recombination context are explicit. The H0–M near degeneracy and the
chosen prior measure prevent an absolute H0 calibration claim. Unknown inherited
producer inversion/interpolation conventions limit an exact software reproduction;
the direct CLASS angular-distance mean defines this new working numerical route.

## Executed 2026-10-09 finite reference

[The native consumer](gaussian_consumer.cpp) retains the pinned Irreducible
Gaussian factor and owns covariance admission, normalization and quadratic/profile
kernels. Its clean SDK source is `5ef0a1627983f1b15199d768bc45b4328702e5ff`,
build `b13ad26785b3a1d77a3614af8f36d3df9a927609a6c56871a95ac42520821040`.
[Python orchestration](point_reference.py) uses the freshly restored CLASS 3.3.0
extension and checks original rows, observer frames, distance duality and an
independent SciPy Gaussian calculation. The frozen attempt performed 36 actual
CLASS background solves and 144 native normalized evaluations at twelve physical
backgrounds and three precision policies, with fixed-M controls and bounded
conditional-M fits. The source/kernel/runtime inventories remain unchanged.

Maximum native/reference `|ΔlnL|` was `5.82077e-11`. Background production-to-first
refinement gave `0.000794108`; first-to-second gave `0.00001464994`, both below the
predeclared `0.01` final-score budget. At the anchor, the conditional magnitude
fit was `M=-19.441156192814535`, normalized `lnL=845.4181036896788`. The best
finite pilot background was `(omega_b,omega_cdm,H0)=(0.02,0.10,60)`,
`M=-19.684930865097435`, `lnL=845.7736855022163`. These are actual data-model
conditional fits, with no global cosmological optimum or qualified posterior.
The original covariance controls, failed attempt, corrections, source/build
policies and full distances/residuals/evaluations are retained together in a 350-file, 87,785,447-byte private selection. The
first canonical publication failed and its partial attempt is retained; no
completion or fresh-restoration claim is made for this relative package. The
separate corrected calibrated-1,657 control package completed publication and
fresh restoration of 36 files; its original covariance refusal remains intact.

The selected released table/covariance originals and runtime dependencies have
exact named custody in the [finite dataset account](../../sources/foundation/data-inventory-2026-10-09.md)
and [pin map](../../sources/foundation/data-custody-pins-2026-10-09.json).
No archives, matrices, installed dependencies or executed receipts enter Git.
Reconstruction uses the preserved build policy and exact restored SDK/CLASS
identities, with new explicit local paths; historical absolute paths are not
portable configuration defaults. This finite pilot does not inherit primary-CMB
posterior qualification or cross-probe independence.

The next posterior requires separately frozen reviewed sampler source, proposal,
prior transformations, seeds, starts, caps and precision policy. An external
mature engine must own acceptance. Numerical refusals inside physical prior
support stop an attempt. Four independent chains, rank diagnostics, bulk/tail
ESS, Monte Carlo error and prior/support checks remain required; current posterior
status is unqualified.

## Separate transformed-sampling preparation

[Coordinates](coordinates.py) use `h=H0/100`,
`u=(omega_b,Omega_cb=(omega_b+omega_cdm)/h²,eta=ln h,calM=M−5log10h)`.
The inverse retains coupled original physical-box membership; no rectangular u
prior or clipping is introduced. Its determinant is `100 exp(3 eta)`, so the
transformed target adds `ln100+3 eta` once. Proposal-density ratios are evaluated
in u, separately. Fixed photons/relics prevent an exact scale-degeneracy claim.
Deterministic roundtrip, coupled-support, normalization and independent Jacobian
controls precede sampling. Endpoint roundoff never enlarges physical support.

[Statistical orchestration](inference.py) delegates centered symmetric pilot or
independence Student-t6 proposals/densities to SciPy and Hastings acceptance to
installed emcee singleton MHMove. Four chains have independent explicit seeds;
all holding states are retained. An injected unit-likelihood control checks the
same transform against known physical uniform means, variances and cross-moments,
with autocorrelation MCSE of each moment. Its thresholds are frozen before use.
A separately bounded real-data pilot is discarded; production proposal geometry
is frozen from actual pilot covariance before chain execution. Rank Rhat<1.01,
bulk/tail ESS≥400 and mean MCSE/SD≤0.05 apply to all reported varying coordinates.
No production posterior qualification is asserted here.
