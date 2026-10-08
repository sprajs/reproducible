# Three-project preservation: 2026-10-08 audit

The private shared bucket now has readable dataset, paper/review, experiment and
engine-evidence collections, with 123 named catalog resources. Historical UUID
snapshots are frozen directory copies retained as backing history; current work
uses the [named layout](shared-data.md) and [startup discovery](cloud-startup.md).
No originals, sealed handover files, receipts or unfinished branches were deleted.

The audit inspected 25 physical roots and 29 Git contexts: 188,918 entries,
13,130,560,906 logical bytes, including ignored stores, custody archives and
unfinished worktrees. Source/reviews/candidates/configs/findings reference Git;
pinned downloads keep URLs/versions/hashes; cheap products keep reconstruction
routes. Valuable failed/accepted evidence, expensive outputs, unavailable inputs
and unique unfinished material have private archival custody. Unknown provenance
remains explicit. Source revision alone does not identify a compiled executable.

The selection preserves 39,299 occurrences as 17,448 unique blobs
(3,431,317,330 bytes), compressed into 15 bundles (1,220,174,219 bytes).
Controls and full indexed provenance bring the upload to 1,416,088,454 bytes.
7,281,406,876 physical bytes were excluded as regenerable products or pinned
cached downloads. Identical bytes are deduplicated, and 94 existing remote
objects cover 213 occurrences without another copy. Logical volume differs from
disk allocation. Third-party public redistribution remains unapproved; private
custody does not override copying restrictions. Credential-marker material was
excluded conservatively, with original containers/receipts kept locally.

All14 sealed files matched; 69/90 named source assets were located by hash.
Ladder FITS-to-f64 structural reconstruction matched all three product hashes;
13 source tars matched exact Git reconstruction and published remote ancestry.
S3 admission/readback checked all50 exact object versions before manifest-last
publication. A fresh pinned restore recovered all39,299 selected occurrences;
every destination was reopened and its length/SHA256 matched. Only this generated
verification copy and our incomplete pack products were removed afterward.

Observations, calibrated reductions, fitted summaries, synthetic controls and
generated results remain distinct. DESI BAO is released fitted compression;
SDSS FLUXCAL is calibrated reduction; ladder/Planck/SN summaries retain their
conditioning. Fixed-design/Gaussian/supplied-drag controls do not establish
observational calibration uncertainty. No scientific gate was relaxed or
qualification inferred from archival or CI checks.

Unresolved: 21 named assets (including optical-template/calibration and historic
likelihood locators), dependence/calibration/selection gaps, five worktree
remnants without usable Git roots, and nine JSON parse failures. Two previously
uncommitted setup files changed during separate authorized infrastructure work;
their original audited hashes remain unresolved and the new Git identities are
recorded separately. Unlocated hash declarations also include compound build
identities; they are not all missing inputs. The detailed private report,
per-entry manifest ledger, dependency map and restrictions are archived together.

## Exact preservation pins

- Completion manifest URI: `s3://research-data-436908790672-eu-west-2/shared/archives/three-project-preservation-2026-10-08/releases/a28b1403e10c0fe48e0e86f61049ccd36d2e2607c8d17a7e8b13004883cb9f0b/manifest.json`.
- SHA256: `d1c5a4585dadedfc29cb25cfd65aef7437590de25004d719dd4848cc8a5f0f7b`.
- VersionId: `nPRYB0JgXuuTY5b5FbYwrXr8RIZmEs_G`.
- Classification manifest SHA256: `a28b1403e10c0fe48e0e86f61049ccd36d2e2607c8d17a7e8b13004883cb9f0b`.

Catalog release URI: `s3://research-data-436908790672-eu-west-2/shared/catalogs/releases/8178a90fae7bba262740f1b568e406c1fec7f9c5ad891862274bb4ab237a81aa.json`; SHA256 `8178a90fae7bba262740f1b568e406c1fec7f9c5ad891862274bb4ab237a81aa`; VersionId `YEZ8wGF_4Qxwo9q3pgrE5Hmj_ZID8HI6`. The discovery pointer `shared/catalogs/research-data.json` may advance; pin the immutable release/resource manifest for reuse.

Use `research_storage.py resolve three-project-preservation-2026-10-08` to
inspect the catalog route. The canonical
[private-preservation restorer](../scripts/restore_preservation.py) retains the
tested archived `restore.py` algorithm, adding explicit restricted-account/root
admission and bundle-path checks. It has its own Git source identity. Supply all three completion pins and
a **new** destination; `--recover-roots` maps selected original occurrences into
`recovered/rootNN/<original-relative-path>`. The manifest root table explains
those recovery IDs. Git-backed, redownloadable and regenerated entries retain
their separate routes; they are not silently substituted into historical attempts.

```sh
python scripts/restore_preservation.py \
  --manifest-uri s3://research-data-436908790672-eu-west-2/shared/archives/three-project-preservation-2026-10-08/releases/a28b1403e10c0fe48e0e86f61049ccd36d2e2607c8d17a7e8b13004883cb9f0b/manifest.json \
  --manifest-sha256 d1c5a4585dadedfc29cb25cfd65aef7437590de25004d719dd4848cc8a5f0f7b \
  --manifest-version-id nPRYB0JgXuuTY5b5FbYwrXr8RIZmEs_G \
  --destination data/restored-preservation --recover-roots
```

Cloud uses `--ambient-credentials` with its own restricted identity. Shared archive
payloads and catalog releases are readable there; access to `irreducible/` resource
metadata is separately scoped. This audit's local readback verified the retained
cloud connection-test object; no cloud scientific execution was performed.
