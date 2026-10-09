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
