# Local cleanup and S3 persistence: 2026-10-09

S3 is the persistent bulk-data store across all three repositories. Git retains source, reviews, candidates, configs and concise findings; ignored local directories are temporary scratch/cache. Every useful completed, failed or partial attempt and unfinished handoff must be published and pinned before the agent ends or hands off work. Blocked copying or upload retains local bytes and an explicit unpreserved blocker.

The owner authorized local cleanup after the preservation upload. Fresh exact-VersionId GET checks covered all50 original archive objects and all17,448 original CAS members. The supplemental input archive recovered all1,197 occurrences, each checked against its original bytes/SHA256. The cleanup plan was published before removal. Historical S3 versions, original receipts, scientific requests/models/SDK pins and Git source were not edited.

## Removed local copies

| Route | Files | Logical bytes |
|---|---:|---:|
| Verified original archive | 28,564 | 5,123,589,670 |
| Verified supplemental inputs | 1,197 | 494,746,725 |
| Recorded reconstruction route | 123,235 | 6,767,291,424 |

Total: **152,996 files, 12,385,627,819 bytes (12.39 GB)**. All inspected Git statuses matched before/after removal. Only empty generated directories were removed. Task-owned staging and readback copies were subsequently removed after their control records were preserved. Logical sizes count original paths and hardlinks, not unique bytes or filesystem allocation.

The first removal attempt stopped at an owner read-only directory. Its original code/log/journal remains archived. The resumed attempt temporarily granted parent write access only to owner-owned directories and restored their permissions; the original remote evidence remains immutable.

## Retained exceptions

The audit retained 186,079,073 bytes without an eligible verified recovery route, including the sealed Prospector container with expired signed-URL material. Credential-marker material was not uploaded. Unique untracked source/notes remain for Git review. Changed/missing-since-audit files and new/active post-audit work were outside deletion authority. The original 21 missing named assets, calibration/selection/covariance gaps and redistribution restrictions remain unresolved. Retaining these exceptions is not a claim that every local file was uploaded.

## Exact S3 audit pins

Use the configured named catalog, or completed-manifest discovery. The original 2026-10-08 preservation pin remains unchanged in [its account](preservation-2026-10-08.md). The new archives use `research-named-manifest/v1`:

- **Supplemental original input copies**: `s3://research-data-436908790672-eu-west-2/shared/archives/three-project-input-caches-2026-10-09/versions/c5bf50cedfc538d97bfa35b704aefd7a797e10a72729e4cc829e7fa96b66e3ab/manifest.json`; SHA256 `0c11214cfab5cff90160471c00e93b128a63e9a0cda6eb029f21a06c8a98de48`; VersionId `WlgzQExNIEyJTBCjeCr_2vInyU6LPDEA`.
- **Completed cleanup journal and recovery references**: `s3://research-data-436908790672-eu-west-2/shared/archives/local-eviction-2026-10-09/versions/b7be2a4e7fd4a827bf3d3ba5d2320a6eccde43d027af3662b257ca828b252bc6/manifest.json`; SHA256 `f6087b69f073bf290322924168fb15b4a5f712fd1b9c1496ed0688e6c29be6c9`; VersionId `QsEUabm_U_Pz63OrIb8d5y1SavWeSTp1`.

Restore supplemental inputs with `scripts/restore_preservation.py`, all three exact named manifest pins above, a **new** destination and optional `--recover-roots`. It retains the original root/path/hash mapping. No historical SDK/model/request is silently substituted. Restore cleanup controls with `research_storage.py pull`; gunzip the removal journal to recover its exact original JSONL bytes. Its prior-plan authority and interrupted/resumed identities are recorded together.

## Future work

Follow [startup discovery](cloud-startup.md) and [the named layout](shared-data.md). Use `push --evict-local` to publish, freshly verify remote bytes, then remove unchanged local regular files; pinned `evict` verifies by default and needs `--apply` to remove. It refuses changed/extra files, linked selections, credential/environment roots, Git-tracked material and uncertain Git ownership.

The restricted cloud identity writes only `reproducible/`. Work from any repo can persist at `reproducible/handoffs/<owner-repository>/<name>` without widening IAM. Retain actual ownership/source/role in provenance; a handoff does not promote a scientific result. `list --collection` finds completed uploads before catalog curation, with explicit pagination.

A local test using the separately restricted `research-cloud` profile passed actual handoff Put/Get, exact manifest/version readback and `--evict-local` removal. This is transport evidence, not a cloud scientific run. The diagnostic pin is:
`s3://research-data-436908790672-eu-west-2/reproducible/handoffs/prospector/storage-contract-check-2026-10-09/versions/2fa0eb535eb0a693f161ef1c3434b34d2b10d2d3cf3cb63c5f6b417df40a449d/manifest.json`; SHA256 `6fc7de100dd18253c1b49384a4e7a67fc3f7f043ca4be1e086b952d268dc606d`; VersionId `XMSCaqKg6amoshE3IaN3DFw8ksBi5TQw`.

No scientific execution or new qualification was performed during cleanup. Source branches, unfinished scientific work and historical Git contexts remain preserved.
