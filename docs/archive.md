# Shared exact-version evidence archive

[archive_experiment.py](../scripts/archive_experiment.py) prepares an explicit
SHA-256/byte inventory, uploads selected valuable evidence to a configured S3
bucket, and restores the exact recorded object versions. Git retains code,
portable configuration and concise findings; full archive manifests and receipts
remain in [ignored runtime storage](storage.md). A successful transport is not a
scientific gate or a permanent research-publication identifier.

Archive costly full attempt records, raw output, failures, immutable configuration
and source/runtime/data identities needed to audit meaningful findings. Select
individual files; there is no recursive directory upload. Exclude reliably
redownloadable source inputs, cheap regenerated products, caches, build trees and
credentials. Keep immutable upstream URL/version/hash acquisition references in
the attempt record instead of copying those source bytes. Review third-party
rights and each selected file for credentials before marking redistribution
approved. The tool rejects common credential paths;
it cannot infer rights, scientific value, secret contents or regeneration cost.

Use relative POSIX paths in inventories and portable bucket/prefix/region config.
Absolute local paths are never recorded by this helper. Existing historical bytes
are not rewritten: actual observed runtime paths in full provenance remain
legitimate evidence. Executable scripts and configuration must derive their
current roots rather than depend on an original workstation. New run artifacts
should include logical paths relative to their attempt root so consumers can
use restored evidence while retaining original observed paths separately. Secret
contents must be excluded from selection.
Do not export AWS keys, profiles or credential-file contents. AWS authentication
uses boto3's standard runtime credential chain (workload role, SSO/profile or
environment supplied outside Git). Install `boto3` in the runtime environment;
the repository's scientific environment and offline checks do not require it.

## Configuration and retention

Provide a real bucket controlled by the collaboration; the helper never invents
or creates a bucket. Configuration has only these fields (`region` is optional):

```json
{
  "schema": 1,
  "bucket": "REPLACE_WITH_CONFIGURED_BUCKET",
  "prefix": "cosmology/evidence",
  "region": "us-east-1",
  "retention": "retain-indefinitely"
}
```

The uppercase placeholder intentionally refuses until replaced with a real S3
bucket name. Commit reviewed nonsecret configuration if useful, or use ignored
`.work/archive-config.json`; never put authentication material in this document.
Readiness/upload require bucket versioning `Enabled` and refuse any enabled
expiration or noncurrent-version-expiration lifecycle rule, conservatively even
if its filter is outside this prefix. No lifecycle configuration is acceptable;
inability to inspect it is a blocker. Upload uses the bucket's configured default
encryption rather than overriding it. A KMS-backed bucket also requires the
runtime identity's appropriate KMS permissions; configure keys/defaults in the
bucket infrastructure rather than this portable evidence record.

The retention policy is indefinite until explicit human review of preserved
findings and replacement archive identities. This helper has no delete,
overwrite-local, lifecycle-edit or versioning-edit command. Versioning is not
Object Lock: administrators can still delete versions or later change lifecycle
rules. Configure organizational access controls and, if required, Object Lock
separately. Keep write access away from delete-version permission; readers need
only exact-version object reads. Uploaders need `s3:GetBucketVersioning`,
`s3:GetLifecycleConfiguration`, `s3:PutObject` and `s3:GetObjectVersion`, scoped to
the chosen bucket/prefix. Restore needs `s3:GetObjectVersion`. Readiness tests
current bucket policy, not future retention or full object write permission.

## Prepare, upload and restore

Write an explicit ignored selection, for example `.work/archive-selection.json`:

```json
{
  "schema": 1,
  "experiment": "lcdm-campaign",
  "attempt": "reviewed-attempt-001",
  "source_revision": "REPLACE_WITH_FULL_REVIEWED_GIT_COMMIT",
  "files": [
    {
      "path": "runs/reviewed-attempt-001/full-attempt.json",
      "evidence_role": "full-attempt-record",
      "reason": "Preserve costly original execution and failure evidence",
      "redistribution": "approved",
      "redownloadable": false,
      "cheap_to_regenerate": false
    }
  ]
}
```

Replace the source revision placeholder with the actual full immutable Git
revision and select the actual valuable raw/config/identity files from the
controller's run inventory. `--root` defines the inventory root; manifests retain
only paths relative to it. A run manifest alone is insufficient if its referenced
valuable output bytes are missing from the selection. Each file is limited to
5 GiB (one S3 PUT); split larger evidence into explicitly identified chunks. One
selection contains at most 1,000 files, keeping the version manifest bounded.

```sh
python scripts/archive_experiment.py prepare --root . --selection .work/archive-selection.json --manifest .work/archive-manifest.json
python scripts/archive_experiment.py readiness --config .work/archive-config.json
python scripts/archive_experiment.py upload --root . --config .work/archive-config.json --manifest .work/archive-manifest.json --receipt .work/archive-receipt.json
python scripts/archive_experiment.py restore --config .work/archive-config.json --receipt .work/archive-receipt.json --destination .work/restored-evidence
```

Preparation hashes every selected regular file. Upload verifies all local bytes
before its first write, then reads and hashes each returned non-null `VersionId`.
The content-addressed remote archive manifest records the original inventory and
each object's key/version; its own key, SHA-256, bytes and version are pinned by
the local receipt. Preserve that small receipt durably alongside the experiment's
archive reference; share it through the agreed secure artifact channel. It
contains no credentials or workstation paths. Full manifests and receipts are
runtime evidence, not new public receipt files for every attempt. Git findings
may cite the `s3://bucket/key`, exact version ID and SHA-256 as an archive reference.
Private S3 evidence does not itself supply a public permanent publication ID.

Restore verifies the remote manifest version/hash before trusting any path, then
downloads the named data versions with bounded byte/hash checks. Matching local
files are verified and reused; changed files, symlinks and traversal paths are
refused. Verified downloads publish atomically without replacing existing files.
An interrupted restore may leave earlier verified files; rerun with the same
receipt. Corrupt partial bytes are removed. A failed upload may leave unreferenced
S3 versions, but publishes no success receipt; preserve these for explicit review
instead of deleting them automatically. Retry with a fresh local receipt path;
existing manifests/receipts are never overwritten.

## Validation and readiness limits

The offline fake-S3 tests exercise exact-version restoration after later object
writes, manifest/data corruption, unsafe paths, local changes, missing versions,
retention refusal and credential-safe diagnostics:

```sh
python -m unittest discover -s tests -p test_archive_experiment.py -v
```

No live bucket, identity or upload was available when this helper was introduced.
Actual shared access remains blocked until the collaboration supplies a bucket
and runtime identity, passes readiness, then performs and checks a small
authorized valuable-evidence upload/restore. Missing runtime credentials fail
explicitly; SDK errors are reported without echoing potentially sensitive details.
