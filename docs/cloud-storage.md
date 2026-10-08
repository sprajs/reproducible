# Shared research storage

The private bucket `research-data-436908790672-eu-west-2` is in London
(`eu-west-2`). S3 grows with use; there is no fixed capacity to reserve.
It has public access blocked, bucket-owner ownership, SSE-S3 encryption,
versioning and a policy requiring HTTPS. Completed objects and old versions
have no automatic expiry. Incomplete multipart uploads are abandoned after
seven days. The $10/month account cost budget emails the owner at 50%, 80%
and 100% actual cost and 100% forecast; credits/refunds are excluded so credits
do not hide underlying usage. This is an alert, not a spending limit.

[storage.json](../storage.json) contains public connection settings, never
credentials. Namespaces separate `reproducible/`, `prospector/`, `irreducible/`
and `shared/`. The local `research` AWS profile has bucket-only read/write
permissions, with no object deletion or account administration. The separate
cloud identity writes only `reproducible/` and reads `reproducible/`, `prospector/`
and `shared/`. No root credentials belong in a research task or cloud setting.

For selected scientific evidence, use the existing [exact-version archive
workflow](archive.md) with [archive-storage.json](../archive-storage.json).
It records individual S3 versions and enforces explicit evidence selection.
The directory snapshot commands below preserve working input/attempt directories
and the initial recovery snapshots; they do not replace those evidence rules.

## Local commands

Install [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
and [rclone](https://rclone.org/install/). Use Python 3.11 or newer. This host has
AWS CLI 2.37.11 and rclone 1.75.1. Each additional computer needs an authorized
AWS identity of its own; a Git clone does not contain credentials. Prefer
short-lived role credentials when the host supports them. For this personal
host, the dedicated access key is in the owner-only `~/.aws/credentials` file.
Revoke/replace that key if the machine is lost; do not copy the local key into
cloud environments. The cloud identity has a separate key.

```sh
python scripts/cloud_storage.py status
python scripts/cloud_storage.py list
python scripts/cloud_storage.py push results/experiment/attempt --label experiment-attempt
python scripts/cloud_storage.py pull SNAPSHOT_ID data/restored --manifest-sha256 MANIFEST_SHA256
```

`push` creates a fresh attempt prefix, hashes the source files, uploads them,
reads every remote file back to calculate SHA-256, rechecks the source, then
uploads a manifest as the completion marker. It prints the snapshot identifier
and manifest hash and saves them in ignored `.work/storage/receipts/`.
Keep that pair in the experiment's concise account when relying on the snapshot.
`list` shows completed manifests. Interrupted prefixes remain without a manifest
and are not completed snapshots. A retry creates a new attempt; it does not edit
the failed one. Existing snapshot contents are immutable by convention and by
this tool's behavior, **not** S3 Object Lock. Versioning allows an administrator
to recover accidental overwrites made with other tools.

`pull` requires the pinned manifest hash and a new destination. It verifies the
manifest and then every restored file, refusing mismatches. An interrupted or
failed restore retains its partial destination for inspection. Empty directories,
permissions, ownership and modification times are not part of the snapshot
contract: this preserves named regular-file bytes. Symlinks, special files and
unsafe paths are refused. Commands are bounded to one hour per subprocess;
two concurrent file transfers and two concurrent multipart parts are used.

Use `--namespace prospector` before the command to archive a deliberately selected
Prospector source/cache directory, or `--namespace shared` for common inputs.
Do not upload an entire home directory, `.aws/`, `.env` files, a virtual environment,
or a repo's mixed `.work/` directory. Source permissions still apply to private
cloud copies. This bucket does not publish papers or provide a public website.

Inputs and run outputs are staged locally for the compiled controllers. After a
run, snapshot its complete attempt directory, including failures. This transport
does not change historical SDK/request pins, scientific gates, or the runner's
execution interface. An upload is not scientific qualification. A private S3 URI
also does not replace a public durable research archive/DOI for publication.

## Initial recovery pins

The initial local input and result directories were uploaded on 2026-10-08.
These are preservation snapshots, not a curated selection or new scientific
qualification. Both now live under `reproducible/snapshots/` in the bucket above;
all objects were checked by SHA-256 after the bucket migration. Historical local
receipts retain the original bucket URI; use this current bucket with the same
snapshot and manifest identities.

- Inputs: `20261008T222558Z-initial-inputs-14883d082b5941ceadcd2fb8508f524a`,
  15 files, 113433757 bytes; manifest SHA-256
  `89297608d3cbd60ce7db1dfc30701b98669964620e7abe1c9dc682365d2135da`.
- Results: `20261008T222559Z-initial-results-caa3617bfa9b4dada6b5658399049c68`,
  503 files, 807313081 bytes; manifest SHA-256
  `8e1c4ded16319159e72df93b606cfe8fd5ef52dd9ac71a2021f8a8eb06eefffe`.

## Current Codex Cloud (Cosmology)

The private `Cosmology` environment includes all three repositories. Request
`AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` as **Personal** environment
variables and supply the separate `reproducible-cloud` identity through the
personal vault for this environment. Never use root or the local identity.
These raw values are visible to the task because AWS signs requests locally.
Proxy-substituted network-secret placeholders cannot replace an AWS signing key.
Do not print environment values or include them in source, prompts or receipts.
Keep environment access set to **Only me** and rotate the key if access changes.

Install AWS CLI and rclone in the environment, then run:

```sh
python /workspace/reproducible/scripts/cloud_storage.py --ambient-credentials status
```

The helper automatically uses standard AWS environment credentials when set.
Read the runtime network policy and preserve its proxy and CA trust. Test an
upload and a pinned-hash restore before claiming the cloud connection works.
Read shared archive manifests under `shared/`; write outputs under
`reproducible/`. Existing tasks keep their own state: publishing an updated
environment does not retrofit tools into a running task.

See the [current cloud environment guide](https://learn.chatgpt.com/docs/environments/cloud-environments)
for personal variables, runtime credentials and publishing behavior.

## Legacy Codex cloud environment

Configure the environment for `sprajs/reproducible`. Install AWS CLI and rclone in
the environment image or setup script. Add these **secrets**, using the separate
`reproducible-cloud` IAM identity, not root or the local identity:

- `RESEARCH_AWS_ACCESS_KEY_ID`
- `RESEARCH_AWS_SECRET_ACCESS_KEY`

The owner-only local handoff file `~/.aws/reproducible-cloud-secrets.json` has
these two values. Copy them into the secret fields directly, never into a chat,
Git commit, plain environment-variable field or setup-script text.

After the existing setup steps, run:

```sh
python scripts/configure_cloud_storage.py
python scripts/cloud_storage.py status
```

The [setup helper](../scripts/configure_cloud_storage.py) deliberately writes a
bucket-scoped `research` profile with file mode 0600, preserving other profiles.
This makes the credential available to the agent's data/result operations after
setup. Anyone with access to that environment can use its research permissions.
Use a private environment. Rotate the key and reset cached environments after
revocation or access changes. Do not persist root credentials there.

[Codex cloud documentation](https://learn.chatgpt.com/docs/environments/cloud-environment)
states that secrets are available only during setup, while environment variables
last throughout the task. Merely adding secrets does not enable runtime uploads;
the explicit restricted-profile setup above is necessary for this workflow.

Enable agent network access to these specific HTTPS domains and methods
GET, HEAD, PUT and POST (listing, authentication and multipart transfer):

- `research-data-436908790672-eu-west-2.s3.eu-west-2.amazonaws.com`
- `s3.eu-west-2.amazonaws.com`
- `sts.eu-west-2.amazonaws.com`

Do not replace an existing allowlist; add the required entries. Package hosts
may also be needed during setup. DELETE is optional for aborting failed multipart
uploads; lifecycle cleanup handles abandoned uploads without granting object
deletion. The AWS IAM policy still excludes `s3:DeleteObject` and
`s3:DeleteObjectVersion` even if a network rule allows DELETE.

For AWS EC2/container environments, prefer an attached role with the same scoped
permissions; invoke `python scripts/cloud_storage.py --ambient-credentials status`
to use the host identity. No long-lived key is needed in that case.
