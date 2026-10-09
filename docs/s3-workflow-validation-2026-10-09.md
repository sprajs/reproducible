# S3 workflow validation checkpoint: 2026-10-09

The existing observational experiment, archive and candidate work remain the starting point. This checkpoint fixes a source-audited input-directory interface and records what still needs execution. It is not a new cosmological result or a new S3 readback report. Date is Europe/London; the audit ran on 2026-10-08 UTC.

## Evidence and current limitation

The attached cloud environment failed before executor attachment: `environment_startup_failed`, underlying `vpn_enrollment_failed` during `vpn_enrollment`; connectivity `offline`. Current runtime status reported the two AWS credential bindings `ready`, but no shell was available to use them. No credential value was inspected. No local checkout/cache/worktree inventory, data download, numerical experiment or new S3 publication was possible in this task. These are `not_attempted: executor_unavailable`, not failed scientific models. Existing credentials/settings were preserved.

Three explicitly requested `gpt-6.1-sol` workers at high reasoning audited separate repository ownership: `/root/irreducible_owner`, `/root/reproducible_owner`, `/root/prospector_owner`. Requested model and launch evidence are known; backend identity was not exposed. Zero local compute jobs were used, respecting the shared four-job ceiling. Another archive-staging chat was active; its transport changes were left intact. Its current status was read, but no thread-messaging tool was available.

Inspected GitHub source heads were Irreducible `e9e33fb938626a53ee8e6b8b4c33523164cc895a`, Reproducible `59ffc242b563eebbc46a0bf00f7de22428191b74`, Prospector `dc19ee04a003e32270a16c30d2de5efeb3bae324`. Their exact-main hosted runs were respectively [37861082598](https://github.com/sprajs/irreducible/actions/runs/37861082598), [37861067378](https://github.com/sprajs/reproducible/actions/runs/37861067378), [37861074790](https://github.com/sprajs/prospector/actions/runs/37861074790), all successful. Those are existing hosted checks, not newly executed science. Irreducible acoustic #57, Apple #58 and fast CI #60 were already merged; do not restart them. Default CI is engineering coverage; full numerical regressions remain explicit.

## What the archive record establishes

The tracked [preservation account](preservation-2026-10-08.md) reports 123 named resources, 50 exact-version object readbacks and restoration of 39,299 selected occurrences with byte lengths and SHA256 verified. It preserves 17,448 unique blobs in 15 compressed bundles; total upload 1,416,088,454 bytes. This task inspected the published Git account and its pins, not the actual private catalog or payload bytes. An earlier cloud [92-byte diagnostic](cloud-startup.md) also verified exact VersionId and SHA256; it does not prove current executor or scientific access.

| Scientific material | Declared route and meaning | Remaining verification |
| --- | --- | --- |
| Paper/source reviews, candidates, configs | Exact Git commit/path; Prospector owns source claims and handoffs | Read selected catalog entry and check candidate/source hashes against the accepted experiment snapshot |
| Released DESI BAO means/covariance | Fitted distance compression with reconstruction/fiducial conditioning; public acquisition pins in the BAO reader | Establish whether catalog contains bytes or acquisition-only route; verify both full13 files before preparing or scoring |
| SDSS FLUXCAL and passband assets | Calibrated reduction; original row/filter/calibration/selection identities matter | Resolve missing calibration/template locators before observational promotion |
| Planck, ladder and SN summaries | Conditioned fitted/released summaries; not additional independent measurements | Preserve calibration, overlap and covariance assumptions; do not multiply unresolved scores |
| Supplied-drag, Gaussian, fixed-design and optical controls | Synthetic or conditional numerical controls | Keep their manifests and findings outside observational success counts |
| Accepted, refused, failed and unfinished attempts | Named experiment/evidence collections or private preservation transport | Restore selected exact manifests with their declared format; inspect original request/build/input identities |

The reported unresolved ledger includes 21 named assets, five worktree remnants without usable Git roots, nine JSON parse failures and two changed uncommitted setup files whose original audited hashes were unavailable. Some unlocated declarations are compound build identities, not missing data. Do not guess provenance or regenerate substitutes under old hashes. Read the private classification/dependency ledger before deciding which entries belong to a new run.

The archive pin is recorded in the preservation account: completion SHA256 `d1c5a4585dadedfc29cb25cfd65aef7437590de25004d719dd4848cc8a5f0f7b`, VersionId `nPRYB0JgXuuTY5b5FbYwrXr8RIZmEs_G`; immutable catalog release SHA256 `8178a90fae7bba262740f1b568e406c1fec7f9c5ad891862274bb4ab237a81aa`, VersionId `YEZ8wGF_4Qxwo9q3pgrE5Hmj_ZID8HI6`. Discovery can advance. These are historical pins, not newly verified ones. The private-preservation restorer restores the full transport; use a selected dataset's authoritative route for a bounded scientific check instead of downloading the 1.42 GB archive. An S3 ETag is never the input content hash.

## Owned gaps and next actions

| Priority / capability | Observed failure or missing prerequisite | Owner | Scientific impact | Next concrete action |
| --- | --- | --- | --- | --- |
| P0 execution portability | VPN enrollment failed before shell; configured AWS bindings cannot be exercised | Cloud environment operator | No new clean-cache, S3 or numerical validation | Attach a working reviewed environment, rerun bounded startup and preserve the discovery receipt; do not change credentials/security as an inferred repair |
| P0 restored observational inputs | Controller originally read `ROOT` at both initial and final admission; acquisition already accepted another root | Reproducible | A correctly restored fresh input directory could not be consumed directly | This change adds `--input-root`, uses it consistently and retains unchanged release/hash/order/covariance gates; require a committed clean real-input run before scientific acceptance |
| P1 actual archive inventory | This task could inspect only Git account/pins, not private catalog bytes | Reproducible, with Prospector source mapping | Dataset/run availability and compatibility remain unverified here | Pin catalog release, resolve one named real dataset, map manifest dependencies and retrieve only selected exact versions under a declared byte cap |
| P1 numerical sensitivity | Quick versus broader optimizer agreement is recorded; aggregate CLASS printed-table/interpolation/ruler error is not certified | Reproducible; native errors belong to Irreducible | A fit bracket cannot establish solver accuracy | Declare per-observable and score tolerances before a bounded baseline/changed-parameter solver-precision study; retain rejected settings and measured shifts |
| P1 usable fitting scope | Existing fit varies only H0 with other physical/nuisance/fluid coordinates fixed; no priors or posterior | Reproducible, Prospector candidate review | Conditional minima cannot establish full-data cosmological conclusions or rule out a model family | Validate the existing one-dimensional fit first, then specify a scientifically identifiable multi-coordinate target and prior/calibration contract |
| P1 native/reference compatibility | Native supplied-drag massless and thermal prerequisites are distinct from full CLASS massive-neutrino/CMB/constant-w states | Irreducible, Prospector | Substituting native approximation would change the tested physics | Keep explicit model IDs and lost scope; compare only supported shared observables with mapped species/densities and earned error allocations |
| P1 SN target | Original source covariance refusal, separately named symmetric working profile and unresolved calibration/selection remain | Reproducible, Prospector source audit | No qualified SN contribution or combined SN/BAO/CMB fit | Resolve original matrix/runtime semantics and measurement residual/calibration law; retain original refusal and repair identity |
| P2 broader probes | Separate primary Planck evaluations are at DESI minima; no lensing likelihood, raw galaxy/window target or calibrated SN target | Reproducible; Prospector specifies claims; Irreducible supplies missing physics | Broader H0 resolution still uses the same probes; cannot fairly test unrelated alternatives | Acquire source-compatible likelihood/data contracts, including lensing reconstruction, clustering/RSD/AP/windows or lower-level SN exposures as required by each candidate |
| P2 provenance/publication | Catalog pointers are mutable; unknown covariance/assets/source remnants persist; cloud writes only reproducible/ | Reproducible, Prospector | Unpinned input or joint ancestry invalidates reconstruction/inference | Retain exact URI/SHA256/VersionId/format, per-file scientific roles and executable identities; publish immutable named attempts with readback and manifest last |

## Advertised paths and pending integration

All new bounded integrations below are `not_attempted: executor_unavailable`. Source classification and hosted fixtures are not observational tests.

| Current packet | Source-declared route | Relevant repository checks / unresolved scope |
| --- | --- | --- |
| expansion-background | Synthetic fixed-redshift CLI | `test_consumer`; clean pinned engine required |
| lcdm-reference | Pinned CLASS predictions and separate official likelihood route | `test_lcdm_reference`, `test_lcdm_prediction`, `test_lcdm_likelihood`; source/build/runtime/input admission |
| lcdm-bao-reference | Fixed-point real full13 compression score | `test_lcdm_bao_reference`; score is not fit or posterior |
| lcdm-baseline; lcdm-campaign | Narrow native supplied-drag/thermal numerical controls | `test_lcdm_baseline`, `test_lcdm_campaign`; faithful full Planck/native closure stays blocked |
| observational-cosmology | Real full13 conditional H0 fits and separate primary-CMB scores | `test_observational_cosmology`; new restored-root actual run still required |
| released-ladder; released-box | Released linear/finite-box numerical contracts | `test_released_ladder`, `test_released_box`; source support, event lineage and posterior/observational qualification remain distinct |
| sdss-released-observer-contract | Source serialization/joins reader | `test_sdss_source_reader`; structural completion does not unblock scientific likelihood |
| sn-observer-passband; sn-symmetric-working-profile | Declared conditional controls/working SN profile | Follow each packet's exact source/SDK checks; retain faithful SN refusal |
| temporal-shared-optical-control | Synthetic photon/detector control | `test_temporal_shared_optical`, `test_temporal_reference_transport`; no observational detector qualification |
| legacy-supernova | Historical route | Preserve historical record; unsupported as a current production pipeline |

There are 13 current experiment directories. No `sis-thin-lens-control` packet exists here; engine lens controls do not create an advertised Reproducible path.

## Reconstruction and next experiment

Start in a clean current checkout with a new ignored input directory, no inherited data cache and one compute job. Use the current [startup guide](cloud-startup.md) and [named storage guide](shared-data.md):

```sh
python3 scripts/storage_startup.py --ambient-credentials
python3 scripts/research_storage.py --ambient-credentials resolve desi-bao-dr2
```

Retain the returned catalog and resource pins and declared restore format. If the resource is acquisition-only, record that fact and follow its pinned acquisition route; it is not proof that observational payload bytes were downloaded from S3. Do not invent a resource manifest, copy workstation files or silently use a synthetic substitute. Record a maximum transfer allowance before downloading; require mean and covariance together. Preparation preserves all13 ordered axes and the full13-by13 covariance.

After exact-byte restoration/admission, reuse the qualified reference runtime only if its full build/source/executable/runtime identities pass; otherwise use the existing pinned bootstrap with one job. The patched interface supports a distinct restored input root:

```sh
python -B experiments/observational-cosmology/controller.py \
  --runtime "$PWD/.work/cosmology-runtime/runtime.json" \
  --input-root "$PWD/.work/s3-quick-inputs" \
  --attempt "$PWD/results/observational-cosmology/s3-quick-UNIQUE" \
  --profile quick --planck --deadline-utc YYYY-MM-DDTHH:MM:SS+00:00
```

This is the next command to validate in an attached executor, not a completed run. Quick keeps all13 real BAO rows, fits H0 on55–85 with nine grid points, at most20 refinements and0.05 bracket tolerance. `broader` keeps exactly the same data and conditioned coordinates, with31 grid points, at most28 refinements and0.01 bracket tolerance; it is broader numerical resolution, not broader probe coverage. Separate official Commander/SimAll/Plik-lite vectors retain their1e-6 gate. Compare the LambdaCDM baseline, changed H0 points and the explicitly named fixed-w variant; add a precision sensitivity configuration only after declaring the numerical acceptance budgets. Keep per-probe scores separate. Render using the existing pinned plot route and verify retrieved products by their recorded hashes.

Publish selected meaningful successful/failed evidence through `research_storage.py --ambient-credentials push` to `reproducible/experiments/observational-cosmology/attempts/UNIQUE`, with explicit provenance and per-file roles for mixed evidence. First run its dry run. Include exact configs, all repo/candidate/source/input hashes, actual executable/build identity, numerical/thread settings, selection/calibration/covariance ancestry, findings, failures and reconstruction commands. Verify exact-VersionId readback of each object and publish the completion manifest last; retain returned URI/SHA256/VersionId. Retrieve that exact attempt into another new directory and replay score/plot checks. No new S3 run/result location exists for this checkpoint.

## Attached-runtime validation: 2026-10-09 UTC

This later execution supersedes the executor-unavailable status above only for
its expressly tested routes; historical observations and pins remain unchanged.
The attached Debian 13 x86_64 runtime rebuilt the original qualified CLASS
`0ceb7a9a4c1e444ef5d5d56a8328a0640be91b18`, native Gaussian SDK
`7a006f81a36a70cdcd3187a1298a8a1ea2cf3f39` and official selected PLC3.01 sources
with one shared compute job and OMP/BLAS threads one. Scientific/tool archives
were hash checked (85,033,189 bytes); local CMake 3.31.6 supplemented the existing
pinned Debian Fortran/header fallback. No scientific source was repinned.

The current catalog DESI entry is acquisition-only. Separately, the authoritative
historical snapshot route restored exact-version S3 payload bytes for both DESI
full13 files and a 47,188-byte released
Pantheon+ REDSHIFT_CMB redshift/velocity-override reduction: selected total
50,207 bytes. Original release lengths/SHA256, final DH/DM ordering and every
covariance entry survived admission. No 1.42GB preservation bundle was fetched;
the historical 39,299-occurrence claim was not repeated as a new full restore.

PR25 head `52aa10f6ff6b94b9ab684e46b61348b42a2dcbc0` passed a real clean committed
consumer run from that empty, external S3-restored input root. Quick plus separate
official Planck completed 42.3335 seconds, with unchanged terminal source/runtime/
data identities; all three official printed-difference checks passed 1e-6. A
separate upstream-acquired fresh-root quick matched the new S3 run's scientific
values exactly; only the latter counts as S3 payload restoration. Both actual
plots rendered under hash-locked dependencies and were visually inspected.
Local 319 tests and repository checks passed. An independent review hashed all 767
attempt files and 570 admitted runtime files without mismatches. PR25 merged at
`df6932cfce2b5029d7f82d136d0037db7cd9d90d`; exact-main Python 3.11/3.13 CI passed
[run 37868620297](https://github.com/sprajs/reproducible/actions/runs/37868620297).

| Actual quick model | Conditional H0 | DESI chi2 | Separate primary Planck raw log likelihood |
| --- | ---: | ---: | ---: |
| Flat LCDM | 68.8331390311 | 10.6410517554 | -626.1937119821 |
| Fixed w=-0.9 PPF | 66.6984504953 | 16.9570944841 | -867.2904518072 |

Each bracket width is 0.03768749 km/s/Mpc; full-output minus fast-policy chi2 is 0.
These actual freshly built values slightly differ from historical printed
results, so no historical executable equality is claimed. CLASS executable
SHA256 is `efb7325bb2e314031195b1b89135b67d9160f58a154e20266c789ad99a106a05`;
Gaussian executable SHA256 is
`c557eb18516a616eee083668be32b4d2f31d1444acc2f5be5d0bdf02ac15f181`;
actual SDK build identity is
`5e77b7eabdf305b413af95400231fe85854e9c191f0328c9c8814008e90f40c2`.
The clean restored quick manifest SHA256 is
`6be05cb70cc1f4dd6925b20388c26d614d5c2e82d92829fbcc68acc09d6e2fa8`.

Before numerical comparisons, a retained protocol set relative drag/BAO budgets
1e-4, DESI chi2 shift 0.01, separate Planck total/component log-likelihood shift 0.2,
and common-axis matter-power shift 0.01. The original source-supplied
`cl_permille.pre` was compared at H0=67.32117,65,75 for both models. Independently,
LCDM H0=67.32117 doubled background_Nloga 40000->80000 or tightened background
integration tolerance 1e-10->1e-11. These axes are distinct from optimizer brackets.

All 14 sensitivity cases executed, but empirical numerical qualification remains
**rejected/incomplete**. Fixed-w H0=75 changes separate primary Planck logL by
+0.29961458 (Plik-lite+0.30007004), exceeding the predeclared 0.2 budget; original
failure is retained. BAO ratios and scores are unchanged under cl_permille. Table
sampling changes BAO ratios by at most 1.477e-7 and chi2 by 0.00028768. Integration
refinement changes BAO ratios by 1.194e-9 and chi2 by 3.134e-7; its printed matter
k axes have no exact common coordinates, so the common-axis Pk gate refuses,
while actual linear-P interpolation diagnostics retained by
`theory.product_difference` remain separately labelled and uncertified. Table
refinement shares only four printed k nodes, so its full-grid Pk qualification
also remains unassessed; passing those four nodes does not qualify a spectrum.
An appended correction preserves the initial common-node assessment and narrows
its stated scope.
No tolerance was weakened and no certified aggregate bound follows. An earlier
sensitivity harness failed pre-CLASS on a missing expected-pin path; it is retained
separately from the corrected new attempt and supplies no physical evidence.

The thirteen packet source inventory and all relevant local fixture checks pass;
they do not turn historical, synthetic or blocked dedicated routes into real
observational integrations. Current native SDK checks likewise cannot substitute
for their historical frozen SDKs. Faithful SN covariance refusal, separately
named symmetric working repair, absent calibrated SN/lensing-reconstruction/
clustering-RSD-AP-window targets and unknown joint dependencies remain blockers.
The demonstrated fit is conditional H0 only, with no posterior or joint score.

The optional broader profile also completed 70.5489 seconds from the same S3 root,
clean source and runtime. It retained full13 and tightened only optimizer
resolution: LCDM H0=68.8313494551, chi2=10.6410259197; fixed-w H0=66.6974207976,
chi2=16.9570784500. Each bracket is 0.00621124 km/s/Mpc. Relative to quick, H0
changes -0.00178958/-0.00102970 and chi2-0.00002584/-0.00001603. Separate primary
Planck values are -626.1547671593/-866.9732922903. This empirical optimizer
comparison supplies neither a solver error bound nor additional probes.
Broader local manifest SHA256 is
`5b6ab31262bf51a2e67eaae0318668d4c1b9aeb1d47fa63da4791098d7d82d1b`.

### Immutable selected quick evidence

The named manifest uses `research-named-manifest/v1`. Its 52 selected generated/
mixed evidence files were admitted by dry run, individually read back by exact
VersionId and content hashes, then the completion manifest was published last.
This is a reconstructable selected evidence bundle, not the complete 767-file raw
CLASS-table attempt; explicit omission/regeneration ancestry is retained within
its provenance. Public input acquisitions retain pinned routes with redistribution rights
unverified.

- URI: `s3://research-data-436908790672-eu-west-2/reproducible/experiments/observational-cosmology/attempts/s3-portability-20261009t011242z-4a339d25d54d/versions/e03b5650ab666196190dfee1bad57718ecf9fed62b0f03de1a425d2917946252/manifest.json`
- SHA256: `0dc9e2739e6dff4353b943f9224da1b2126f5776d83243b9f1d1a27bf8ed8697`
- VersionId: `GKI3otD.skAKbaO4i1SBDvA14Spv.7VK`

The attached prepared runtime was activated with
`source /workspace/.setup/activate.sh`; that environment-specific activation
supplies prepared tool paths; restricted ambient credentials remained unchanged.
A distinct build used the explicit local CMake3.31.6 path; scientific source pins
remain in the preserved runtime record. New machine reconstruction starts with
its prepared-tool activation, `storage_startup.py --ambient-credentials` and the
exact named-manifest pull route; an example path is not a portable credential
binding. The direct LCDM reference command requires the ignored parent
`results/lcdm-reference` to exist before its fresh attempt can be admitted.

The advertised `experiments/lcdm-reference/run.py` command was also exercised
directly with a runtime configuration binding that same exact CLASS build.
After creating its required ignored parent directory, all four anchor/precision/
ns-minus/ns-plus cases completed in 28.5281 seconds. Prediction execution passed;
its own gates retain inference/interpretation blocked and numerical scope only
empirical differences. Anchor drag is 147.054261 Mpc at z=1059.928342. Maximum
precision TT/EE/TE differences are 0.4618998/0.0102618/0.0369075 microkelvin squared.
The direct prediction record SHA256 is
`2e4250667abb2912fd626320ad6ec23f32b7be91bcfe52b4a139df9294692e78`.
The first invocation's missing-parent pre-admission refusal is preserved
separately; it created no attempt directory and supplies no scientific evidence.

That exact quick manifest was pulled into another empty directory; all 52 selected
objects passed exact-VersionId length/SHA256 checks. Saved DESI fits and separate
Planck scores were retrieved unchanged. A distinct plotting replay copied the
retrieved product JSONs and rerendered without recomputing physics: both PNGs
matched the original SHA256 exactly (`ed359670e39a20716938ae042f0c074ae213a65838d44ae2f84a9531b2280dbc`
for DESI fit and `e11e7e1ae4be0a11f2f92164e8be749b22e3875ef7a347de9b418b1bf7f8ec3d`
for predictions). Thus published score/plot retrieval was actually tested rather
than inferred from upload success.

The selected numerical bundle preserves the original failed pre-CLASS harness,
corrected fourteen-case execution, rejected qualification and appended Pk scope
correction, exact source/protocol/config snapshots, and broader optimizer profile.
It uses the same named-manifest format; its original attempts are not rewritten.

- URI: `s3://research-data-436908790672-eu-west-2/reproducible/experiments/observational-cosmology/attempts/numerical-sensitivity-20261009t011616z-31db979e7eee/versions/78a895946a7d2f942158c116389a808a5645ae018143f612f6514e13f84aae30/manifest.json`
- SHA256: `8146db5abc70788728655b80af1579460dd822490b808200ab20717186d07f7b`
- VersionId: `ibqwkuXstnqemUQIMHclvTQ9pByisOOM`

All 128 selected numerical evidence objects were individually verified through
exact-version readback before manifest-last completion. Transfer/retrieval checks
establish preservation, not acceptance of its deliberately retained numerical
failures. The same private-preservation rights scope remains explicit.

The direct four-case reference and its preserved pre-admission failure have a
separate selected evidence bundle (47 objects, exact readback, manifest last):

- URI: `s3://research-data-436908790672-eu-west-2/reproducible/experiments/lcdm-reference/attempts/direct-reference-20261009t011834z-95c992a81e24/versions/4febdabea8c7fbf4661570894961de626f26a9347d108317233b92ea19a44f0c/manifest.json`
- SHA256: `f565c4662574f032e910068c8bc9fcedd5d4adedff9e3d616e578799bd58f5f1`
- VersionId: `j9.re66X3FCuTtdoyEiAyftnRA0lBWl0`

Independent empty-directory pulls of the numerical and direct-reference named
manifests also completed: 128 and 47 selected files respectively. Comparison of
original staging inventories with all three fresh retrieved bundles verified 227
files with zero SHA256 mismatches. This includes failed attempt 001 source/protocol,
original qualification, appended correction, broader optimizer results and the
direct command's refused prefix. Scientific run records were not rewritten.
Worker model/launch evidence and shared job allocations accompany the bundles;
all scientific builds/runs used one serial job with one OMP/BLAS thread.
