#!/usr/bin/env python3
"""Archive selected evidence with exact S3 versions; never acquire credentials in Git."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile


class ArchiveError(ValueError):
    """An archive contract or integrity check failed."""


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True, allow_nan=False) + "\n").encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def exact_keys(value, required, optional=()):
    if not isinstance(value, dict) or set(value) - set(required) - set(optional) or set(required) - set(value):
        raise ArchiveError("Unexpected or missing record fields")


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ArchiveError("Duplicate JSON field")
        result[key] = value
    return result


def decode(data):
    try:
        return json.loads(data, object_pairs_hook=unique_pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(ArchiveError("Nonfinite JSON")))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ArchiveError("Invalid JSON record") from exc


def read_json(path):
    return decode(Path(path).read_bytes())


def text(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 1000 or any(ord(c) < 32 for c in value):
        raise ArchiveError("Expected bounded nonempty text")


def sha_value(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ArchiveError("Invalid SHA-256 identity")


def relative(value):
    text(value)
    if "\\" in value or not value.isascii():
        raise ArchiveError("Paths must use portable ASCII slash components")
    parts = value.split("/")
    if any(p in ("", ".", "..") or ":" in p for p in parts) or PurePosixPath(value).is_absolute():
        raise ArchiveError("Unsafe relative path")
    for part in parts:
        lower = part.lower()
        if lower in {".aws", ".ssh", ".git", "credentials", "id_rsa", "id_ed25519"} or lower.startswith(".env") or lower.endswith((".pem", ".key")):
            raise ArchiveError("Credential or private control paths cannot be archived")
    return value


def safe_path(root, name):
    relative(name)
    root = Path(root)
    if root.is_symlink():
        raise ArchiveError("Root cannot be a symlink")
    root = root.resolve()
    current = root
    for part in name.split("/"):
        current = current / part
        if current.is_symlink():
            raise ArchiveError("Symlink archive paths are refused")
    if not current.resolve().is_relative_to(root):
        raise ArchiveError("Archive path leaves root")
    return current


def identity(path):
    if not path.is_file():
        raise ArchiveError("Evidence must be a regular file")
    with path.open("rb") as stream:
        hashed = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"bytes": path.stat().st_size, "sha256": hashed}


def evidence(row, hashed=False):
    required = {"path", "evidence_role", "reason", "redistribution", "redownloadable", "cheap_to_regenerate"}
    exact_keys(row, required | ({"bytes", "sha256"} if hashed else set()))
    relative(row["path"])
    for name in ("evidence_role", "reason"):
        text(row[name])
    if row["redistribution"] != "approved" or row["redownloadable"] is not False or row["cheap_to_regenerate"] is not False:
        raise ArchiveError("Only approved, valuable, nonrepeatable evidence may be archived")
    if hashed:
        if type(row["bytes"]) is not int or not 0 <= row["bytes"] <= 5 * 1024 ** 3:
            raise ArchiveError("Byte count must fit one S3 PUT (at most 5 GiB); split larger evidence explicitly")
        sha_value(row["sha256"])


def validate_manifest(value, hashed=True):
    exact_keys(value, {"schema", "experiment", "attempt", "source_revision", "files"})
    if type(value["schema"]) is not int or value["schema"] != 1:
        raise ArchiveError("Unsupported manifest schema")
    for field in ("experiment", "attempt"):
        if not isinstance(value[field], str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}", value[field]):
            raise ArchiveError("Invalid experiment or attempt identifier")
    if not isinstance(value["source_revision"], str) or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", value["source_revision"]):
        raise ArchiveError("An immutable source revision is required")
    if not isinstance(value["files"], list) or not value["files"] or len(value["files"]) > 1000:
        raise ArchiveError("Expected a bounded explicit evidence inventory")
    names = set()
    for row in value["files"]:
        evidence(row, hashed)
        name = row["path"]
        if name in names or any(name.startswith(p + "/") or p.startswith(name + "/") for p in names):
            raise ArchiveError("Duplicate or conflicting evidence paths")
        names.add(name)


def write_new(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".archive-", suffix=".partial", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def prepare(root, selection, output):
    validate_manifest(selection, hashed=False)
    manifest = dict(selection)
    manifest["files"] = [dict(row, **identity(safe_path(root, row["path"]))) for row in selection["files"]]
    validate_manifest(manifest)
    write_new(output, canonical(manifest))
    return digest(canonical(manifest))


def validate_config(config):
    exact_keys(config, {"schema", "bucket", "prefix", "retention"}, {"region"})
    if type(config["schema"]) is not int or config["schema"] != 1 or config["retention"] != "retain-indefinitely":
        raise ArchiveError("Expected schema 1 and retain-indefinitely policy")
    bucket = config["bucket"]
    if not isinstance(bucket, str) or not re.fullmatch(r"[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]", bucket) or ".." in bucket or re.fullmatch(r"[0-9.]+", bucket):
        raise ArchiveError("Expected a configured S3 bucket name")
    relative(config["prefix"])
    if "region" in config and (not isinstance(config["region"], str) or not re.fullmatch(r"[a-z0-9-]{1,64}", config["region"])):
        raise ArchiveError("Invalid runtime region")


def runtime_client(config):
    validate_config(config)
    try:
        import boto3
    except ImportError as exc:
        raise ArchiveError("Install boto3 in the runtime environment; it is optional for offline checks") from exc
    try:
        session = boto3.Session(region_name=config.get("region"))
        credentials = session.get_credentials()
        if credentials is None:
            raise ArchiveError("AWS runtime credentials unavailable; configure the standard AWS credential chain")
        credentials.get_frozen_credentials()
        return session.client("s3")
    except ArchiveError:
        raise
    except Exception as exc:
        raise ArchiveError("AWS runtime credential resolution failed; check the standard AWS credential chain") from exc


def ready(client, config):
    validate_config(config)
    if client.get_bucket_versioning(Bucket=config["bucket"]).get("Status") != "Enabled":
        raise ArchiveError("S3 bucket versioning must be Enabled")
    try:
        lifecycle = client.get_bucket_lifecycle_configuration(Bucket=config["bucket"])
    except Exception as exc:
        if getattr(exc, "response", {}).get("Error", {}).get("Code") != "NoSuchLifecycleConfiguration":
            raise
        lifecycle = {}
    for rule in lifecycle.get("Rules", []):
        if rule.get("Status") == "Enabled" and ("Expiration" in rule or "NoncurrentVersionExpiration" in rule):
            raise ArchiveError("Automatic version expiration conflicts with indefinite evidence retention")


def version(value):
    if not isinstance(value, str) or not value or value == "null" or len(value) > 1024 or any(ord(c) < 32 for c in value):
        raise ArchiveError("S3 must return an explicit non-null VersionId")
    return value


def receive(client, config, key, version_id, expected, stream):
    response = client.get_object(Bucket=config["bucket"], Key=key, VersionId=version(version_id))
    body = response["Body"]
    try:
        if response.get("VersionId") != version_id or response.get("ContentLength") != expected["bytes"]:
            raise ArchiveError("S3 response version or byte count differs")
        count = 0
        hashed = hashlib.sha256()
        while block := body.read(min(1024 * 1024, expected["bytes"] - count + 1)):
            count += len(block)
            if count > expected["bytes"]:
                raise ArchiveError("S3 response exceeds recorded byte count")
            hashed.update(block)
            stream.write(block)
        if count != expected["bytes"] or hashed.hexdigest() != expected["sha256"]:
            raise ArchiveError("S3 object integrity check failed")
    finally:
        body.close()


def verify_remote(client, config, key, version_id, expected):
    # Avoid buffering large objects while checking the exact uploaded version.
    with open(os.devnull, "wb") as sink:
        receive(client, config, key, version_id, expected, sink)


def upload(client, config, root, manifest, receipt_path):
    validate_config(config)
    validate_manifest(manifest)
    if Path(receipt_path).exists():
        raise ArchiveError("Receipt exists; preserve the immutable attempt")
    manifest_sha = digest(canonical(manifest))
    # Verify the entire inventory and key bounds before the first remote write.
    for row in manifest["files"]:
        if len(f'{config["prefix"]}/evidence/{manifest_sha}/{row["path"]}'.encode()) > 1024:
            raise ArchiveError("Evidence path and configured prefix exceed the S3 key limit")
        if identity(safe_path(root, row["path"])) != {k: row[k] for k in ("bytes", "sha256")}:
            raise ArchiveError("Local evidence differs from the prepared manifest")
    ready(client, config)
    objects = []
    for row in manifest["files"]:
        key = f'{config["prefix"]}/evidence/{manifest_sha}/{row["path"]}'
        path = safe_path(root, row["path"])
        with path.open("rb") as stream:
            result = client.put_object(Bucket=config["bucket"], Key=key, Body=stream,
                                      Metadata={"sha256": row["sha256"]})
        version_id = version(result.get("VersionId"))
        verify_remote(client, config, key, version_id, row)
        if identity(path) != {k: row[k] for k in ("bytes", "sha256")}:
            raise ArchiveError("Local evidence changed during upload; no receipt published")
        objects.append({"path": row["path"], "key": key, "version_id": version_id})
    archive = {"schema": 1, "manifest_sha256": manifest_sha, "manifest": manifest, "objects": objects}
    data = canonical(archive)
    if len(data) > 16 * 1024 * 1024:
        raise ArchiveError("Remote archive manifest exceeds restoration bound; no receipt published")
    archive_sha = digest(data)
    key = f'{config["prefix"]}/manifests/{archive_sha}.json'
    result = client.put_object(Bucket=config["bucket"], Key=key, Body=data,
                              Metadata={"sha256": archive_sha})
    version_id = version(result.get("VersionId"))
    verify_remote(client, config, key, version_id, {"bytes": len(data), "sha256": archive_sha})
    receipt = {"schema": 1, "bucket": config["bucket"], "prefix": config["prefix"],
               "key": key, "version_id": version_id, "bytes": len(data), "sha256": archive_sha}
    write_new(receipt_path, canonical(receipt))
    return receipt


def validate_receipt(config, receipt):
    exact_keys(receipt, {"schema", "bucket", "prefix", "key", "version_id", "bytes", "sha256"})
    sha_value(receipt["sha256"])
    version(receipt["version_id"])
    if (type(receipt["schema"]) is not int or receipt["schema"] != 1
            or receipt["bucket"] != config["bucket"] or receipt["prefix"] != config["prefix"]
            or receipt["key"] != f'{config["prefix"]}/manifests/{receipt["sha256"]}.json'
            or type(receipt["bytes"]) is not int or not 0 < receipt["bytes"] <= 16 * 1024 * 1024):
        raise ArchiveError("Receipt conflicts with configuration or manifest bounds")


def restore(client, config, receipt, destination):
    import io
    validate_config(config)
    validate_receipt(config, receipt)
    content = io.BytesIO()
    receive(client, config, receipt["key"], receipt["version_id"], receipt, content)
    archive = decode(content.getvalue())
    exact_keys(archive, {"schema", "manifest_sha256", "manifest", "objects"})
    manifest = archive["manifest"]
    validate_manifest(manifest)
    manifest_sha = digest(canonical(manifest))
    if type(archive["schema"]) is not int or archive["schema"] != 1 or archive["manifest_sha256"] != manifest_sha:
        raise ArchiveError("Archive manifest identity differs")
    if not isinstance(archive["objects"], list) or len(archive["objects"]) != len(manifest["files"]):
        raise ArchiveError("Archive version inventory differs")
    # Admit all remote and destination paths before restoring any file.
    for row, obj in zip(manifest["files"], archive["objects"]):
        exact_keys(obj, {"path", "key", "version_id"})
        version(obj["version_id"])
        if obj["path"] != row["path"] or obj["key"] != f'{config["prefix"]}/evidence/{manifest_sha}/{row["path"]}':
            raise ArchiveError("Archive object leaves the declared evidence inventory")
        target = safe_path(destination, row["path"])
        if target.exists() and identity(target) != {k: row[k] for k in ("bytes", "sha256")}:
            raise ArchiveError("Existing destination differs; preserved without replacement")
    for row, obj in zip(manifest["files"], archive["objects"]):
        target = safe_path(destination, row["path"])
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(prefix=".archive-", suffix=".partial", dir=target.parent)
        temporary = Path(name)
        try:
            with os.fdopen(fd, "wb") as stream:
                receive(client, config, obj["key"], obj["version_id"], row, stream)
            # Atomic no-clobber publication after verification.
            os.link(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare")
    prep.add_argument("--root", required=True)
    prep.add_argument("--selection", required=True)
    prep.add_argument("--manifest", required=True)
    for name in ("upload", "restore", "readiness"):
        sub = commands.add_parser(name)
        sub.add_argument("--config", required=True)
        if name == "upload":
            sub.add_argument("--root", required=True)
            sub.add_argument("--manifest", required=True)
            sub.add_argument("--receipt", required=True)
        if name == "restore":
            sub.add_argument("--receipt", required=True)
            sub.add_argument("--destination", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            sha = prepare(args.root, read_json(args.selection), args.manifest)
            print(json.dumps({"status": "prepared", "manifest_sha256": sha}))
        else:
            config = read_json(args.config)
            client = runtime_client(config)
            if args.command == "readiness":
                ready(client, config)
            elif args.command == "upload":
                upload(client, config, args.root, read_json(args.manifest), args.receipt)
            else:
                restore(client, config, read_json(args.receipt), args.destination)
            print(json.dumps({"status": args.command + "-verified"}))
        return 0
    except ArchiveError as exc:
        print(json.dumps({"status": "refused", "reason": str(exc)}))
    except Exception:
        # SDK/OS exceptions can contain credentials, URLs or workstation paths.
        print(json.dumps({"status": "refused", "reason": "Runtime I/O or AWS operation failed; no credential details exported"}))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
