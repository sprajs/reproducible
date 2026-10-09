# Reproducible capability and data gaps

Evidence inventory dated 2026-10-09, audited at
`bc5de0da41e8136dfe9b4852f3a792692d556e73`. This is factual readiness and missing
contracts; [roadmap.md](roadmap.md) is the sole active plan. No new scientific
runs, source-paper findings or universal dataset availability claims are created
by this reset. Claims below separate implementation, numerical checks, source
admission, inference and physical interpretation.

## Current baseline and inference

| Gap ID / milestone | Evidence at the audited revision | Consequence / owner |
|---|---|---|
| R-B01 / M0–M1 released target | [CLASS reference](../experiments/lcdm-reference/reference.json) fixes a source point and ns-only cases; [official scorer](../experiments/lcdm-reference/score.py) fixes A_planck=1 and keeps posterior null. Bootstrap selects Commander, SimAll and Plik-lite only. | No source-complete six-coordinate/nuisance posterior or reproduction of full-Plik-plus-reconstruction Table 2. Prospector specifies the released target; Reproducible accepts parameters/priors/assets. |
| R-B02 / M1 numerical domain | [Observed sensitivity account](s3-workflow-validation-2026-10-09.md#attached-runtime-validation-2026-10-09-utc) retains fixed-w H0=75 Planck logL shift +0.29961458 versus predeclared 0.2; full-grid matter-k comparison remains unearned. | An alternative's rejected domain is not a ΛCDM-domain failure, but current optimizer agreement supplies no solver certificate. Reproducible owns score/domain qualification; Irreducible owns native numerical owners. |
| R-B03 / M1 fitting and convergence | [Conditional fit](../experiments/observational-cosmology/controller.py) varies H0 alone over 55–85 at fixed shape; golden-search width is finite optimization resolution. No prior/uncertainty interval, joint target or sampler is returned. Existing theory admits only the anchor/ns ± 0.005; likelihood admission fixes A_planck=1 and Plik-lite, so a varied fit requires a new reviewed adapter identity. | No fully varied cosmological posterior, chains/convergence/MCSE or released posterior reproduction. No accepted fit contract yet distinguishes numerical refusals inside prior support from physical prior exclusions. Reproducible owns inference orchestration. |
| R-B04 / M2 joint target | Optional official primary scores are separate evaluations at DESI minima; fixed-point BAO/SN controls remain separate. | No simultaneous common-parameter joint likelihood, overlap treatment, calibrated tension significance or posterior predictive validation. Reproducible composes only source-admitted factors; Prospector reviews applicability/dependence. |
| R-B05 / M3 native full model | Massless/supplied-drag and thermal supplied-drag packets are distinct from external CLASS species/recombination/primordial/CMB state. | Numerical controls do not earn native full-CMB/physical-drag/transfer/polarization/lensing or native released baseline. Irreducible owns closures/interfaces, Reproducible comparison consumers. |
| R-B06 / M5 comparison | Fixed w=-0.9 is conditional, not a varied extension family. Six-model and fluid/population native sweeps fit no observations. | No fair same-data prior/nuisance-complete alternative posterior or theory-combination inference. Prospector owns compatibility; Irreducible physics; Reproducible fitting. |

## Complete current experiment coverage

There are 15 experiment directories and 11 generic experiment.json packets.
Dedicated source/reference/controller routes do not all use the generic packet
runner, and a blocked generic route can retain separately executed controls.

| Route | Actual retained result or supported operation | Qualification limit |
|---|---|---|
| [expansion-background](../experiments/expansion-background/README.md) | Single compiled chosen flat background at eight redshifts; optional plot | Synthetic, no observation or fit |
| [lcdm-baseline](../experiments/lcdm-baseline/README.md) | Ordered full13 DESI, supplied-drag massless native ratios/density versus Decimal reference | Full Planck/species/drag/CMB and observational compression applicability blocked |
| [lcdm-campaign](../experiments/lcdm-campaign/README.md) | Massless/massive thermal supplied-drag controls, 34 comparisons; corrected references/tails retained | Diagnostic historical 19-scope map; direct distance/ruler allocation unexercised, no posterior |
| [lcdm-reference](../experiments/lcdm-reference/README.md) | Four CLASS prediction cases, separate official primary score route | Fixed/source ns cases; no full released target, lensing likelihood, posterior or native CMB |
| [lcdm-bao-reference](../experiments/lcdm-bao-reference/README.md) | Four fixed-point full13 covariance scores and independent arithmetic | Identical background corpus gives no refinement; printed ruler/interpolation limits remain |
| [observational-cosmology](../experiments/observational-cosmology/README.md) | Real full13 conditional H0 minima; separate Planck scores; actual S3-input and plot retrieval | Same data in quick/broader; rejected/incomplete numerical sensitivity, no joint posterior |
| [released-ladder](../experiments/released-ladder/README.md) | Original 3492-row/47-column source GLS, host joins, contrast variance, synthetic mean responses; narrowed fixed44 target | Unresolved physical44, four joins, selection/constraint and held-out covariance; no physical systematic H0 reconstruction |
| [released-box](../experiments/released-box/README.md) | Original 3492 covariance, fixed44=0/active46 conditional box normalization/marginal controls | Mathematical measure is conditional, not qualified physical ladder/H0 posterior |
| [sdss-released-observer-contract](../experiments/sdss-released-observer-contract/README.md) | Structural 321 source joins / 115-record signed photometry slice and discrepancies | Event/frame/exposure/clock/physical unit/extraction calibration unresolved |
| [sn-observer-passband](../experiments/sn-observer-passband/README.md) | 321 released redshift pairs, chosen coasting/radiation-free ΛCDM and passband synthetic-source integral | No measured source/calibration/released likelihood or posterior |
| [sn-symmetric-working-profile](../experiments/sn-symmetric-working-profile/README.md) | All 1657 selected occurrences on a separately declared symmetric working covariance, full-mode reference | Original nonsymmetric matrix refused; working projection is a changed scientific target |
| [temporal-shared-optical-control](../experiments/temporal-shared-optical-control/README.md) | Supplied synthetic common optical law, exposures, selection/nondetection/refusal; 169 comparisons | No measured template/calibration/detector/population law |
| [native-model-campaign](../experiments/native-model-campaign/README.md) | Six distinct native models; 54 cases, 280/630 rows; restored 92-file evidence | Aggregate rejected/incomplete from constraint residual and NFW conditioning failures; no observed fit/global bound |
| [native-fluid-population](../experiments/native-fluid-population/README.md) | Chaplygin/Plummer grids; 32 cases, 512/1608 rows; 11 endpoint/refusal controls; restored 68-file evidence | Synthetic finite grid; ambiguous q=1 support retained; no perturbation/observational/global certificate |
| [legacy-supernova](../experiments/legacy-supernova/README.md) | Historical claim/correction account and exact prior snapshot | Retired Python pipeline; higher-accuracy likelihood did not converge to tight reported tolerances |

No current SIS thin-lens observational packet exists. Isolated NFW/Hernquist or
self-gravitating Plummer laws do not identify a measured joint mass/light/kinematic
system; added potentials change the Plummer DF's assumptions.

## Dataset declarations, working caches and custody

The exact-byte [asset ledger](../sources/actual-data-asset-status-v2.md) retains
90 assets in 11 families, 19 historical scopes, 15 receipt maps and 22 source pins.
The legacy transport retains391 frozen identities. These source documents preserve
dated availability and explicit role/covariance/rights limits, not fresh payload
verification. The 2026-10-08 preservation account reports 69/90 located and 21
unresolved at its own review. Those dates/methods cannot be merged into a new count.

The primary and isolated audit checkouts have no data/ or results/; inspected
primary cache directories contain plotting/font caches. That bounded local check
makes no global or S3 absence claim. Existing worktrees and originals are retained.

Storage startup passed at 2026-10-09T03:01:07.696295+00:00, pinning 125 catalog
entries: URI
`s3://research-data-436908790672-eu-west-2/shared/catalogs/releases/7ee8a1ce4443bf87b58af95e895ab14b02976d2567186ccd4133b384ce528fcb.json`,
SHA256 `7ee8a1ce4443bf87b58af95e895ab14b02976d2567186ccd4133b384ce528fcb`,
VersionId `5zhtxcsv0MqKPSUGnkvHAXTcIQ307K2T`, 198,929 bytes.
This planning audit inspected that previously verified catalog record, without a
new remote verification. All 11 family resources below use research-resource/v1
metadata with authoritative restore routes; they are not proof of input payload
availability. Selected older input/attempt restores retain their own exact pins
in the linked preservation and experiment accounts.

| Gap ID / family and catalog name | Present in Git / local cache / S3 or acquisition evidence | Scientific source/dependence gap |
|---|---|---|
| R-D01 DESI / desi-bao-dr2 | 2 exact full13 mean/cov identities in Git; no bounded local data; catalog resource metadata, historically acquisition-only named data; actual earlier snapshot restored both exact input payloads | Fiducial/template/reconstruction/windows/scale cuts/compression validity, BOSS/DESI overlap; dimensionless ratios/full covariance are fitted compression |
| R-D02 CMB / cmb-assets; planck-reference | 6 historical CMB locators plus1 marginalized Planck reference; selected CLASS/PLC/data acquisition pins and score archives; no new payload verification | Complete target/prior/nuisance/BBN conventions, primary versus lensing/ACT masks/beams/foreground/reconstruction/overlap; marginal posterior is not an independent measurement |
| R-D03 ladder / released-ladder | 12 ledger assets, compact FITS/design/primary tables; no bounded local data; source-ledger catalog and historical preservation route | Physical44, source rows 2630/2744/2745/2754, N1365 46/45, SMC143/145, HSTLMC69/70, analysis variants/anchors and held-out crosscovariance |
| R-D04 SN distances / released-supernova-distances | 5 ledger assets,1701 source occurrences / 1550 source SNe, fullSTAT+SYS identities; no bounded local data; metadata/preservation route | Original389 / selected 361 unequal covariance pairs; faithful producer semantics, calibrated residuals, duplicate events, training/calibrator/selection ancestry |
| R-D05 SDSS / sdss-released-photometry | 12 ledger assets,321 joins and115-record PHOT slice; 3 dated receipt-only unresolved locations; no bounded local data; catalog route | 19 blank TUNIT and no EXPTIME, 10 RA discrepancies; native exposure/event/frame/clock/FLUXCAL-to-physical/extraction/error/covariance law |
| R-D06 optical / optical-template | 32 template/calibration/passband assets; 16 dated receipt-only unresolved locations; no bounded local data; source-ledger/preservation route | 102 axes versus 105 prose, 8 NA / 2 headers, nominalMODEL000/generator/index bridge, trained spectral-time surface units/errors/crosscovariance and detector/population law |
| R-D07 clustering / boss-rsd | 2 paper/source-description assets; no current catalog/random/window/fullcov/author likelihood admitted; catalog metadata | P0/P2/B0/AP/fiducial/bias/scale/window/mocks, source equation ambiguities, P nested in P+B, same-galaxy BAO and unread 8×8 crosscovariance |
| R-D08 strong lens / lens-b1608 | 4 paper/proposal/inference-description assets; no matched actual pixels/delays/Keck/environment likelihood admitted; catalog metadata | PSF/dust/light/mass-sheet, aperture/templates/anisotropy/external convergence/selection and image/delay/kinematic dependence; rights unreviewed |
| R-D09 thermal / thermal-sources | 12 source/scalar/code assets; 13 exact/evaluated/chosen unit classes; no cosmic abundance probability law admitted; catalog metadata | H/He kinetics/late opacity/BBN/rate uncertainty and shared constants ancestry; chosen scalar values are not independent observations |
| R-D10 HST / hst-dark | 2 derived dark assets, historical archive member hashes and legacy detector inputs; no bounded local data; catalog route | Exact instrument/readclock/units/CALWF3/configuration/gain/noise/extraction/calibration; not transferable into SDSS camera law |
| R-D11 historical NIR/flux/age/time | Legacy: 296 RAISIN, 25 DES flux, 11 signed, 9 CSP, 3 ages, 3 predictors, 3 calibration, 2 timing plus detector groups; acquisition/archive declarations only here | Historical labels/paths are not current source laws, executable inputs or selected independent observations |
| R-D12 future independent disciplines / M4 |No current dedicated weak-shear, siren, chronometer, cluster-count, Lyα forest, 21cm/line-intensity or BBN-abundance observational packet found; availability not assessed | Exact raw/reduced measurement, estimator, survey/systematic/selection and crossprobe/prior/rights contract absent |

## Observation and combination contracts

| Gap ID / milestone | Factual missing contract | Owner and consequence |
|---|---|---|
| R-S01 / M2 overlap | Planck primary/lensing/ACT share sky/instrument/reconstruction; clustering summaries may share galaxies/mocks; SN/SH0ES/templates/calibration share events and reductions. | Prospector/Reproducible: independence is not supplied by distinct filenames. Unknown material dependence blocks a claimed joint subset; a sourced negligible-dependence approximation needs sensitivity evidence. |
| R-S02 / M2 predictive/tension | No released-target predictive draws, held-out common-noise contract, source-qualified systematic H0 distribution or calibrated tension test exists. | Reproducible: conditional contrast variance and synthetic constraint shifts do not provide observational calibration uncertainty. |
| R-S03 / M4 measured optical population | Reduced flux/template surfaces/offset covariance do not define source evolution, extinction, instrument response, nondetection and survey population selection. | Prospector supplies source law; Reproducible measurement/reduction/likelihood; Irreducible physical kernels. |
| R-S04 / M4 clustering applicability | Supplied sigma8/growth and BAO distances do not provide transfer/primordial amplitude or an AP/window/bias/reconstruction likelihood. | Prospector/Reproducible estimator source, Irreducible supported physical predictions. |
| R-S05 / M4 strong lens identifiability | Halo background distances do not determine source light, velocity dispersion, mass sheet/environment or their selected covariance. | Prospector/Reproducible measured system and inference; Irreducible common-potential geometry/kinematics. |
| R-S06 / M5 combinations | Finite background/halo response models lack a shared action/conservation/initial-state owner for proposed combinations; native sweeps supply no full CMB/LSS inference. | Prospector/Irreducible source/stability/compatibility closure precedes Reproducible same-target inference. |

## Engineering, tests and preservation

There are 24 test modules covering runner/packet contracts, covariance/reference
controls, source/SDK/runtime admission, failure retention, metadata decoding,
bootstrap and transport. CI runs Python 3.11/3.13 checks without scientific data
acquisition or native rebuilds. Passing those checks does not establish a sampler,
released posterior, joint data applicability or physical source calibration.
Controllers call actual compiled libraries/external solvers; references remain
separately identified numerical checks, with shared source ancestry declared.

| Gap ID / milestone | Current implementation / retained limit | Owner |
|---|---|---|
| R-E01 / M6 custody granularity | Named push/pull verifies exact versions and publishes manifest last; bounded listing exposes completion markers; catalog resources can be metadata/acquisition/historical transport. | Reproducible canonical transport with identical three-repo copies; each experiment retains its exact format/route, selected-versus-complete scope and lawful reconstruction. |
| R-E02 / M6 portable identity | Historical consumer/request/SDK paths and source budgets remain frozen. Source commit alone is not executable identity. | Reproducible admits clean source/build/executable/toolchain/input identities before/after each new attempt; no automatic historical repin. |
| R-E03 / M6 resource/performance | Existing coarse controllers have bounded process/memory/evidence limits; four shared jobs, normally one per consumer. No new general framework or distributed scheduler is required by current evidence. | Root coordinates jobs; each owner measures matched-quality workload/runtime and cache ownership before optimization. |
| R-E04 / source budget | Audited public tree 2,359,164 bytes versus 2.25 MiB (2,359,296), 132 bytes spare; source-only roadmap/gaps exceed that allowance. | This reset explicitly reviews a 2.5 MiB source-only allowance in [storage.md](storage.md); bulk/generated exclusions, eight-file packets and historical science budgets stay intact. |

Exact archive pins and original successful/failed attempts remain in
[preservation](preservation-2026-10-08.md), [cleanup](local-cleanup-2026-10-09.md),
[attached-runtime evidence](s3-workflow-validation-2026-10-09.md) and the experiment
accounts. This audit does not refresh all payloads, rerun prior science, or
promote uploaded bytes into observational qualification.
