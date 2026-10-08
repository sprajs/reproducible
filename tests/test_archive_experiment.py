"""Offline exact-version, evidence-policy and hostile-path archive checks."""
import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import archive_experiment as archive


class FakeS3:
    def __init__(self):
        self.objects = {}
        self.versioning = "Enabled"
        self.lifecycle = {"Rules": []}
        self.gets = []
        self.return_version = True

    def get_bucket_versioning(self, **kwargs):
        return {"Status": self.versioning}

    def get_bucket_lifecycle_configuration(self, **kwargs):
        return self.lifecycle

    def put_object(self, Bucket, Key, Body, **kwargs):
        data = Body.read() if hasattr(Body, "read") else Body
        versions = self.objects.setdefault((Bucket, Key), {})
        version_id = f"version-{len(versions) + 1}"
        versions[version_id] = data
        return {"VersionId": version_id} if self.return_version else {}

    def get_object(self, Bucket, Key, VersionId):
        self.gets.append((Key, VersionId))
        data = self.objects[(Bucket, Key)][VersionId]
        return {"Body": io.BytesIO(data), "ContentLength": len(data), "VersionId": VersionId}


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        self.source.mkdir()
        self.payload = b"valuable failed-attempt raw output\n"
        (self.source / "output.json").write_bytes(self.payload)
        (self.source / "empty.log").write_bytes(b"")
        self.selection = {"schema": 1, "experiment": "lcdm-campaign", "attempt": "failed-001",
                          "source_revision": "a" * 40, "files": []}
        for name in ("output.json", "empty.log"):
            self.selection["files"].append({"path": name, "evidence_role": "attempt-output",
                                           "reason": "Preserve a costly failed attempt",
                                           "redistribution": "approved", "redownloadable": False,
                                           "cheap_to_regenerate": False})
        self.config = {"schema": 1, "bucket": "offline-test-bucket", "prefix": "cosmology/evidence",
                       "retention": "retain-indefinitely"}
        self.client = FakeS3()
        self.manifest_path = self.root / "manifest.json"
        self.receipt_path = self.root / "receipt.json"

    def prepared(self):
        archive.prepare(self.source, self.selection, self.manifest_path)
        return archive.read_json(self.manifest_path)

    def uploaded(self):
        return archive.upload(self.client, self.config, self.source, self.prepared(), self.receipt_path)

    def test_round_trip_uses_original_versions_even_after_new_latest_objects(self):
        receipt = self.uploaded()
        for bucket, key in list(self.client.objects):
            self.client.put_object(Bucket=bucket, Key=key, Body=b"new latest version")
        destination = self.root / "restored"
        manifest = archive.restore(self.client, self.config, receipt, destination)
        self.assertEqual((destination / "output.json").read_bytes(), self.payload)
        self.assertEqual((destination / "empty.log").read_bytes(), b"")
        self.assertTrue(all(version_id == "version-1" for _, version_id in self.client.gets))
        self.assertNotIn(str(self.root), archive.canonical(manifest).decode())
        self.assertNotIn(str(self.root), archive.canonical(receipt).decode())
        before = len(self.client.gets)
        archive.restore(self.client, self.config, receipt, destination)
        self.assertEqual(len(self.client.gets), before + 1)  # existing files checked locally

    def test_policy_refuses_repeatable_or_unlicensed_evidence(self):
        for field, value in (("redownloadable", True), ("cheap_to_regenerate", True),
                             ("redistribution", "unknown"), ("redownloadable", 0)):
            with self.subTest(field=field, value=value):
                selection = copy.deepcopy(self.selection)
                selection["files"][0][field] = value
                with self.assertRaises(archive.ArchiveError):
                    archive.prepare(self.source, selection, self.manifest_path)
                self.assertFalse(self.manifest_path.exists())

    def test_unsafe_paths_duplicates_and_symlinks_refused(self):
        for name in ("../escape", "/absolute", "a//b", "./output.json", "a\\b", "C:/file",
                     ".env", ".aws/credentials", "key.pem", "a/../b"):
            with self.subTest(name=name), self.assertRaises(archive.ArchiveError):
                archive.safe_path(self.source, name)
        selection = copy.deepcopy(self.selection)
        selection["files"].append(selection["files"][0])
        with self.assertRaisesRegex(archive.ArchiveError, "Duplicate"):
            archive.prepare(self.source, selection, self.manifest_path)
        (self.source / "link").symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(archive.ArchiveError, "Symlink"):
            archive.safe_path(self.source, "link/stolen.json")

    def test_change_before_upload_refused_before_any_remote_write(self):
        manifest = self.prepared()
        (self.source / "output.json").write_bytes(b"changed")
        with self.assertRaisesRegex(archive.ArchiveError, "differs"):
            archive.upload(self.client, self.config, self.source, manifest, self.receipt_path)
        self.assertEqual(self.client.objects, {})
        self.assertFalse(self.receipt_path.exists())

    def test_missing_versioning_or_expiring_versions_refused(self):
        for status in ("Suspended", None):
            self.client.versioning = status
            with self.subTest(status=status), self.assertRaisesRegex(archive.ArchiveError, "versioning"):
                archive.ready(self.client, self.config)
        self.client.versioning = "Enabled"
        for field in ("Expiration", "NoncurrentVersionExpiration"):
            self.client.lifecycle = {"Rules": [{"Status": "Enabled", field: {"Days": 7}}]}
            with self.subTest(field=field), self.assertRaisesRegex(archive.ArchiveError, "expiration"):
                archive.ready(self.client, self.config)
        self.client.lifecycle = {"Rules": [{"Status": "Disabled", "Expiration": {"Days": 7}}]}
        archive.ready(self.client, self.config)

    def test_missing_lifecycle_config_allowed_but_access_denied_not_ignored(self):
        class ServiceError(Exception):
            def __init__(self, code):
                self.response = {"Error": {"Code": code}}
        for code in ("NoSuchLifecycleConfiguration", "AccessDenied"):
            with patch.object(self.client, "get_bucket_lifecycle_configuration", side_effect=ServiceError(code)):
                if code == "AccessDenied":
                    with self.assertRaises(ServiceError):
                        archive.ready(self.client, self.config)
                else:
                    archive.ready(self.client, self.config)

    def test_null_put_version_refused_and_no_success_receipt(self):
        self.client.return_version = False
        with self.assertRaisesRegex(archive.ArchiveError, "VersionId"):
            self.uploaded()
        self.assertFalse(self.receipt_path.exists())

    def test_corrupt_upload_version_refused(self):
        original = self.client.put_object
        def corrupt(**kwargs):
            response = original(**kwargs)
            self.client.objects[(kwargs["Bucket"], kwargs["Key"])][response["VersionId"]] = b"corrupt"
            return response
        with patch.object(self.client, "put_object", side_effect=corrupt), self.assertRaises(archive.ArchiveError):
            self.uploaded()
        self.assertFalse(self.receipt_path.exists())

    def test_corrupt_data_restore_leaves_no_destination_or_partial(self):
        receipt = self.uploaded()
        for (_, key), versions in self.client.objects.items():
            if key.endswith("/output.json"):
                versions["version-1"] = b"!" * len(self.payload)
        destination = self.root / "restored"
        with self.assertRaisesRegex(archive.ArchiveError, "integrity"):
            archive.restore(self.client, self.config, receipt, destination)
        self.assertEqual(list(destination.iterdir()), [])

    def test_manifest_version_and_content_identity_checked(self):
        receipt = self.uploaded()
        versions = self.client.objects[(self.config["bucket"], receipt["key"])]
        versions[receipt["version_id"]] = b"!" * receipt["bytes"]
        with self.assertRaisesRegex(archive.ArchiveError, "integrity"):
            archive.restore(self.client, self.config, receipt, self.root / "restored")
        self.assertFalse((self.root / "restored").exists())
        with patch.object(self.client, "get_object", return_value={"Body": io.BytesIO(b""), "ContentLength": receipt["bytes"], "VersionId": "wrong"}), self.assertRaisesRegex(archive.ArchiveError, "version"):
            archive.restore(self.client, self.config, receipt, self.root / "restored")

    def test_existing_changed_destination_is_not_overwritten(self):
        receipt = self.uploaded()
        destination = self.root / "restored"
        destination.mkdir()
        target = destination / "output.json"
        target.write_bytes(b"valuable local change")
        with self.assertRaisesRegex(archive.ArchiveError, "preserved"):
            archive.restore(self.client, self.config, receipt, destination)
        self.assertEqual(target.read_bytes(), b"valuable local change")
        self.assertFalse((destination / "empty.log").exists())

    def test_immutable_local_manifests_and_receipts(self):
        self.prepared()
        with self.assertRaises(FileExistsError):
            archive.prepare(self.source, self.selection, self.manifest_path)
        self.receipt_path.write_bytes(b"existing receipt")
        with self.assertRaisesRegex(archive.ArchiveError, "Receipt exists"):
            archive.upload(self.client, self.config, self.source, archive.read_json(self.manifest_path), self.receipt_path)
        self.assertEqual(self.client.objects, {})

    def test_receipt_cannot_redirect_bucket_or_key(self):
        receipt = self.uploaded()
        for field, value in (("bucket", "another-bucket"), ("key", "unrelated/object"), ("bytes", True)):
            changed = dict(receipt, **{field: value})
            before = len(self.client.gets)
            with self.subTest(field=field), self.assertRaises(archive.ArchiveError):
                archive.restore(self.client, self.config, changed, self.root / "restored")
            self.assertEqual(len(self.client.gets), before)

    def test_remote_manifest_paths_and_version_inventory_admitted_before_restore(self):
        receipt = self.uploaded()
        base = archive.decode(self.client.objects[(self.config["bucket"], receipt["key"])][receipt["version_id"]])
        for change in ("traversal", "foreign-key", "missing-object"):
            value = copy.deepcopy(base)
            if change == "traversal":
                value["manifest"]["files"][0]["path"] = "../escape"
            elif change == "foreign-key":
                value["objects"][0]["key"] = "another-prefix/private.json"
            else:
                value["objects"].pop()
            data = archive.canonical(value)
            changed = dict(receipt, bytes=len(data), sha256=archive.digest(data))
            changed["key"] = f'{self.config["prefix"]}/manifests/{changed["sha256"]}.json'
            self.client.objects[(self.config["bucket"], changed["key"])] = {changed["version_id"]: data}
            destination = self.root / "restored"
            with self.subTest(change=change), self.assertRaises(archive.ArchiveError):
                archive.restore(self.client, self.config, changed, destination)
            self.assertFalse(destination.exists())

    def test_restore_symlink_destination_refused(self):
        receipt = self.uploaded()
        destination = self.root / "restored"
        destination.mkdir()
        (destination / "output.json").symlink_to(self.source / "output.json")
        with self.assertRaisesRegex(archive.ArchiveError, "Symlink"):
            archive.restore(self.client, self.config, receipt, destination)
        self.assertEqual((self.source / "output.json").read_bytes(), self.payload)

    def test_oversize_file_identity_refused_before_remote_write(self):
        manifest = self.prepared()
        manifest["files"][0]["bytes"] = 5 * 1024 ** 3 + 1
        with self.assertRaisesRegex(archive.ArchiveError, "5 GiB"):
            archive.upload(self.client, self.config, self.source, manifest, self.receipt_path)
        self.assertEqual(self.client.objects, {})

    def test_oversize_s3_key_refused_before_remote_write(self):
        manifest = self.prepared()
        config = dict(self.config, prefix="p" * 1000)
        with self.assertRaisesRegex(archive.ArchiveError, "key limit"):
            archive.upload(self.client, config, self.source, manifest, self.receipt_path)
        self.assertEqual(self.client.objects, {})

    def test_strict_json_and_closed_config(self):
        with self.assertRaisesRegex(archive.ArchiveError, "Duplicate"):
            archive.decode(b'{"schema":1,"schema":1}')
        with self.assertRaises(archive.ArchiveError):
            archive.decode(b'{"bytes":NaN}')
        with self.assertRaises(archive.ArchiveError):
            archive.validate_config(dict(self.config, aws_secret_access_key="never-export"))

    def test_missing_runtime_credentials_are_clear_and_diagnostics_hide_sdk_details(self):
        session = types.SimpleNamespace(get_credentials=lambda: None)
        fake_boto = types.SimpleNamespace(Session=lambda **kwargs: session)
        with patch.dict(sys.modules, {"boto3": fake_boto}), self.assertRaisesRegex(archive.ArchiveError, "credentials unavailable"):
            archive.runtime_client(self.config)
        config_path = self.root / "config.json"
        config_path.write_bytes(archive.canonical(self.config))
        output = io.StringIO()
        with patch.object(archive, "runtime_client", side_effect=RuntimeError("secret-and-workstation-path")), contextlib.redirect_stdout(output):
            result = archive.main(["readiness", "--config", str(config_path)])
        self.assertEqual(result, 1)
        self.assertNotIn("secret-and-workstation-path", output.getvalue())
        self.assertEqual(json.loads(output.getvalue())["status"], "refused")


if __name__ == "__main__":
    unittest.main()
