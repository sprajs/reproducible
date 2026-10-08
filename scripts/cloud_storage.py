#!/usr/bin/env python3
"""Copy immutable research snapshots to S3 and restore verified bytes; no physics."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'storage.json'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def safe_path(name):
    if (not isinstance(name, str) or not name or name.startswith('/')
            or any(ord(c) < 32 or ord(c) == 127 for c in name)
            or '\\' in name or any(p in ('', '.', '..') for p in name.split('/'))):
        raise ValueError('Unsafe snapshot path')
    return PurePosixPath(name)


def inventory(root):
    if root.is_symlink() or not root.is_dir():
        raise ValueError('Source must be a real directory')
    rows = []
    for path in sorted(root.rglob('*')):
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode) or not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
            raise ValueError(f'Symlinks and special files are refused: {path}')
        name = path.relative_to(root).as_posix()
        safe_path(name)
        if stat.S_ISREG(mode):
            before = path.stat()
            sha = digest(path)
            after = path.stat()
            if (before.st_size, before.st_mtime_ns, before.st_ino) != (
                    after.st_size, after.st_mtime_ns, after.st_ino):
                raise ValueError(f'Source changed during hashing: {path}')
            rows.append({'path': name, 'bytes': after.st_size, 'sha256': sha})
    if not rows:
        raise ValueError('Empty snapshots are refused')
    return sorted(rows, key=lambda r: r['path'])


def validate_manifest(doc):
    if not isinstance(doc, dict) or doc.get('schema') != 'research-snapshot-v1':
        raise ValueError('Unsupported snapshot manifest')
    rows = doc.get('files')
    if not isinstance(rows, list) or not rows:
        raise ValueError('Missing snapshot files')
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {'path', 'bytes', 'sha256'}:
            raise ValueError('Invalid file record')
        safe_path(row['path'])
        if row['path'] in seen:
            raise ValueError('Duplicate snapshot path')
        seen.add(row['path'])
        if type(row['bytes']) is not int or row['bytes'] < 0:
            raise ValueError('Invalid file size')
        if not isinstance(row['sha256'], str) or not re.fullmatch('[0-9a-f]{64}', row['sha256']):
            raise ValueError('Invalid SHA-256')
    for name in seen:
        if any(str(p) in seen for p in PurePosixPath(name).parents):
            raise ValueError('Conflicting file and directory paths')
    return sorted(rows, key=lambda r: r['path'])


def run(args):
    result = subprocess.run(args, text=True, capture_output=True, timeout=3600)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or 'Cloud command failed')
    return result.stdout


class Storage:
    def __init__(self, namespace):
        self.config = json.loads(CONFIG.read_text())
        if namespace not in self.config['namespaces']:
            raise ValueError('Unknown namespace')
        self.namespace = namespace
        self.profile = os.environ.get('AWS_PROFILE')
        if not self.profile and not (os.environ.get('AWS_ACCESS_KEY_ID')
                                    or os.environ.get('AWS_WEB_IDENTITY_TOKEN_FILE')
                                    or os.environ.get('AWS_CONTAINER_CREDENTIALS_RELATIVE_URI')
                                    or os.environ.get('AWS_CONTAINER_CREDENTIALS_FULL_URI')):
            # EC2 instance roles can be selected with --ambient-credentials.
            self.profile = self.config['local_profile']
        self.base = f":s3:{self.config['bucket']}/{namespace}/snapshots"

    def aws(self, *args):
        command = ['aws', *args, '--region', self.config['region'], '--no-cli-pager', '--output', 'json']
        if self.profile:
            command += ['--profile', self.profile]
        return json.loads(run(command))

    def check_identity(self):
        identity = self.aws('sts', 'get-caller-identity')
        if identity['Account'] != self.config['account_id'] or identity['Arn'].endswith(':root'):
            raise ValueError('Use a restricted research identity in the configured account, not root')
        return identity

    def rclone(self, *args):
        command = ['rclone', *args, '--s3-provider', 'AWS', '--s3-region', self.config['region'],
                   '--s3-env-auth', '--s3-no-check-bucket', '--s3-force-path-style=false',
                   '--transfers', '2', '--checkers', '4', '--s3-upload-concurrency', '2',
                   '--retries', '2', '--low-level-retries', '3']
        if self.profile:
            command += ['--s3-profile', self.profile]
        return run(command)

    def verify_remote(self, remote, rows):
        # Downloads every object's bytes: do not treat an ETag or metadata as SHA-256.
        output = self.rclone('hashsum', 'SHA-256', remote, '--download')
        found = {}
        for line in output.splitlines():
            if not re.match(r'^[0-9a-f]{64}  ', line):
                raise ValueError('Invalid remote SHA-256 listing')
            sha, name = line[:64], line[66:]
            safe_path(name)
            if name in found:
                raise ValueError('Duplicate remote path')
            found[name] = sha
        if found != {r['path']: r['sha256'] for r in rows}:
            raise ValueError('Remote snapshot bytes do not match source SHA-256 inventory')

    def push(self, source, label):
        if not re.fullmatch('[a-z0-9][a-z0-9-]{0,63}', label):
            raise ValueError('Label must be lowercase letters, digits and hyphens (1-64 characters)')
        rows = inventory(source)
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        snapshot = f'{stamp}-{label}-{uuid.uuid4().hex}'
        remote = f'{self.base}/{snapshot}'
        # A unique attempt prefix keeps concurrent machines and failed attempts separate.
        if self.rclone('lsf', remote, '--recursive').strip():
            raise ValueError('Snapshot destination already contains objects')
        print(f'Uploading {len(rows)} files, {sum(r["bytes"] for r in rows)} bytes as {snapshot}', flush=True)
        self.rclone('copy', str(source), remote + '/files', '--immutable', '--checksum')
        self.verify_remote(remote + '/files', rows)
        if inventory(source) != rows:
            raise ValueError('Source changed during upload; uncommitted remote attempt retained')
        doc = {'schema': 'research-snapshot-v1', 'snapshot': snapshot,
               'namespace': self.namespace, 'created_utc': stamp, 'files': rows}
        with tempfile.TemporaryDirectory() as temporary:
            manifest = Path(temporary) / 'manifest.json'
            manifest.write_text(json.dumps(doc, indent=2) + '\n')
            expected = digest(manifest)
            # Commit marker appears only after full remote byte verification.
            self.rclone('copyto', str(manifest), remote + '/manifest.json', '--immutable', '--checksum')
            check = Path(temporary) / 'readback.json'
            self.rclone('copyto', remote + '/manifest.json', str(check))
            if digest(check) != expected:
                raise ValueError('Manifest readback failed')
        receipt = {'snapshot': snapshot, 'manifest_sha256': expected,
                   'namespace': self.namespace,
                   'uri': f"s3://{self.config['bucket']}/{self.namespace}/snapshots/{snapshot}/manifest.json"}
        records = ROOT / '.work' / 'storage' / 'receipts'
        records.mkdir(parents=True, exist_ok=True)
        with (records / (snapshot + '.json')).open('x') as stream:
            json.dump(receipt, stream, indent=2)
            stream.write('\n')
        print(json.dumps(receipt, indent=2))

    def pull(self, snapshot, destination, expected):
        if not re.fullmatch(r'[A-Za-z0-9-]+', snapshot):
            raise ValueError('Invalid snapshot identifier')
        if not re.fullmatch('[0-9a-f]{64}', expected):
            raise ValueError('Supply the pinned manifest SHA-256 from the upload record')
        if destination.exists() or destination.is_symlink():
            raise ValueError('Restore destination must not exist')
        remote = f'{self.base}/{snapshot}'
        with tempfile.TemporaryDirectory() as temporary:
            manifest = Path(temporary) / 'manifest.json'
            self.rclone('copyto', remote + '/manifest.json', str(manifest))
            if digest(manifest) != expected:
                raise ValueError('Manifest SHA-256 mismatch')
            doc = json.loads(manifest.read_text())
            rows = validate_manifest(doc)
            if doc.get('snapshot') != snapshot or doc.get('namespace') != self.namespace:
                raise ValueError('Manifest identity mismatch')
            destination.mkdir(parents=True, exist_ok=False)
            self.rclone('copy', remote + '/files', str(destination), '--immutable', '--checksum')
            if inventory(destination) != rows:
                raise ValueError('Restored bytes failed verification; partial destination retained')
        print(f'Verified {len(rows)} files at {destination}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--namespace', default='reproducible', choices=['reproducible', 'prospector', 'irreducible', 'shared'])
    parser.add_argument('--ambient-credentials', action='store_true', help='Use environment/container/instance credentials instead of the local profile')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('status')
    commands.add_parser('list')
    push = commands.add_parser('push')
    push.add_argument('source', type=Path)
    push.add_argument('--label', required=True)
    pull = commands.add_parser('pull')
    pull.add_argument('snapshot')
    pull.add_argument('destination', type=Path)
    pull.add_argument('--manifest-sha256', required=True)
    args = parser.parse_args()
    try:
        storage = Storage(args.namespace)
        if args.ambient_credentials:
            storage.profile = None
        identity = storage.check_identity()
        if args.command == 'status':
            storage.rclone('lsf', storage.base, '--dirs-only')
            print(json.dumps({'identity': identity['Arn'], **storage.config}, indent=2))
        elif args.command == 'list':
            print(storage.rclone('lsf', storage.base, '--recursive', '--files-only', '--include', '*/manifest.json'), end='')
        elif args.command == 'push':
            storage.push(args.source, args.label)
        elif args.command == 'pull':
            storage.pull(args.snapshot, args.destination, args.manifest_sha256)
    except (ValueError, RuntimeError, OSError, subprocess.TimeoutExpired) as error:
        parser.exit(1, f'Storage operation failed: {error}\n')


if __name__ == '__main__':
    main()
