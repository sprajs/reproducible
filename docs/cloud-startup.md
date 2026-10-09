# Storage discovery when a chat starts

Every research chat should know the storage location without relying on chat
history or account-wide bucket discovery. Read `AGENTS.md`,
[storage-layout.json](../storage-layout.json) and [shared-data.md](shared-data.md).
The same layout and transport live in all three repositories. Reproducible owns
this startup check; invoke it from the Reproducible checkout even when working
in Prospector or Irreducible.

The private bucket is `research-data-436908790672-eu-west-2`, region `eu-west-2`.
The discovery pointer is `shared/catalogs/research-data.json`. The selected
scientific evidence archive uses `reproducible/evidence/`. Bucket-root listing,
account-wide bucket discovery and `cosmology/evidence/` are not needed and are
outside the cloud identity's granted scope. A 403 there does not prove that
configured data access is broken.

## Startup instructions for the Cosmology environment

Keep the existing science install/start instructions. Add this storage step
before data-dependent work, without rebuilding engines or running experiments:

1. Read the cloud-environment runtime skill. Preserve the inherited proxy and
   CA trust. Use the environment's existing personal AWS signing credentials;
   never print them, copy them to files, or use root. This identity can read
   `shared/`, `prospector/`, `irreducible/` and `reproducible/`, and write only `reproducible/`.
   Engine evidence and shared catalog publication require the separate authorized
   local identity. A fresh computer needs its own authorized credentials.
2. Find the existing Reproducible checkout, normally `/workspace/reproducible`.
   Read its current storage config and docs. If these files are absent, fetch
   `origin/main` and inspect the tracked files there. Update only a clean main
   checkout by fast-forward; preserve branches, existing edits and historical
   experiment pins. Do not use an old documentation placeholder or ask the user
   to rediscover a bucket already specified by the repository.
3. Ensure Python 3.11+ and AWS CLI v2 are available. Install missing tools during
   environment preparation from official verified sources or trusted packages,
   preserving existing tools. Record their versions. The named transport needs
   no daemon, plugin, mount or rclone; historical snapshot restoration additionally
   needs rclone. Do not persist AWS credentials in a published filesystem.
4. Run the bounded read-only discovery check:

   ```sh
   python3 /workspace/reproducible/scripts/storage_startup.py --ambient-credentials
   ```

   Locally, omit `--ambient-credentials` to use the restricted `research` profile.
   Each invocation records a new ignored `.work/storage/startup/*/discovery.json`.
   Exit zero means identity, retention and the exact-version catalog fetch passed.
   It does not test writes, restore all datasets, or qualify scientific evidence.
5. Use the returned catalog entries or `research_storage.py resolve NAME` to
   select a dataset. Pin its authoritative manifest URI, SHA256, VersionId and
   restore route in the attempt. Restore only the selected inputs to a fresh
   ignored directory and verify every byte. A mutable discovery pointer is never
   a scientific input pin. Local paths remain temporary scratch/cache; S3 is the persistent bulk-data store.
6. If access or the catalog is unavailable, retain the failed startup receipt
   and report that specific blocker before starting work that needs the data.
   An unpublished catalog can be bypassed only with an already recorded exact
   manifest/version/hash and its documented restore route. Do not silently
   redownload, substitute data, widen IAM permissions, or claim preservation.
7. After meaningful successful or failed work, push the deliberately selected
   attempt to its named collection, retaining the returned manifest pins after
   remote byte checks. Read-only startup does not make automatic uploads happen.
   Catalog curation is separate from uploading an attempt. Use `list --collection`
   for completed uploads not yet in the catalog. Before ending or handing off
   useful work, publish full failed/partial evidence and unique unfinished state
   too. Record exact pins in Git or an S3 handoff; local paths cannot be the only
   cross-run record. If publication is blocked, retain bytes and report the
   unpreserved state. Evict scratch only after fresh byte checks.

## Publishing the reusable setup

Save changes in the environment editor, verify the setup, then republish and
start a new task. Existing tasks retain their own state. Repository instructions
travel with Git; environment-owned install/start changes require the editor's
save/publish flow. Local personal skills are not synced automatically.
See the [official environment guide](https://learn.chatgpt.com/docs/environments/cloud-environments).
If setup provisioning fails, keep the draft and report it as unpublished; a
successful normal cloud task does not prove that an edit draft can be published.

## Verified cloud transport

A normal Cosmology task authenticated as `reproducible-cloud`, listed the
`reproducible/evidence/` prefix, uploaded 92 bytes and downloaded its exact version
with matching SHA256. This diagnostic is retained at:

- Key: `reproducible/setup-checks/20261008T231108Z-da3438951a3e422893734b7e1e051cf6/diagnostic.txt`
- VersionId: `UCm7GM.AZgN7pectGILf0cDtFRRUJ4Su`
- SHA256: `7b84a8c14c96d8991b6d9421f0701e19729dd9613dbe886ada567f1f4ee6e742`

This records transport evidence; each new runtime must still check discovery.
