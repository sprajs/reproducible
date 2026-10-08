#!/usr/bin/env python3
"""Check shared storage discovery without downloading datasets or uploading data."""
import argparse
from datetime import datetime, timezone
import json
import os
import signal
from pathlib import Path
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]


def run_check(command, credential_args):
    try:
        process = subprocess.Popen(
            [sys.executable, str(ROOT / 'scripts/research_storage.py'),
             *credential_args, command],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            start_new_session=(os.name == 'posix'),
        )
    except OSError:
        return {'status': 'failed', 'reason': 'Could not start storage helper'}
    try:
        stdout, _ = process.communicate(timeout=90)
    except subprocess.TimeoutExpired:
        # The helper starts AWS CLI children. Kill our own process group so
        # inherited pipes cannot keep the timeout handler waiting on a child.
        if os.name == 'posix':
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        else:
            process.kill()
        process.communicate()
        return {'status': 'failed', 'reason': 'Timed out after 90 seconds'}
    if process.returncode:
        # Do not copy arbitrary subprocess output into a durable receipt.
        return {'status': 'failed', 'reason': 'Storage check failed; check AWS CLI, restricted credentials and network access'}
    try:
        return {'status': 'passed', 'result': json.loads(stdout)}
    except json.JSONDecodeError:
        return {'status': 'failed', 'reason': 'Storage helper returned invalid JSON'}


def startup(destination, credential_args):
    destination.mkdir(parents=True, exist_ok=False)
    config = json.loads((ROOT / 'storage-layout.json').read_text())
    receipt = {
        'schema': 'research-storage-startup/v1',
        'checked_at': datetime.now(timezone.utc).isoformat(),
        'bucket': config['bucket'], 'region': config['region'],
        'catalog_pointer': config['catalog_pointer'],
        'checks': {}, 'ready': False,
    }
    receipt['checks']['access'] = run_check('status', credential_args)
    if receipt['checks']['access']['status'] == 'passed':
        receipt['checks']['catalog'] = run_check('catalog', credential_args)
        receipt['ready'] = receipt['checks']['catalog']['status'] == 'passed'
    else:
        receipt['checks']['catalog'] = {'status': 'not_attempted'}
    # Catalog entries and the immutable catalog pin are kept together. This is
    # discovery evidence, not permission to replace a historical scientific pin.
    path = destination / 'discovery.json'
    with path.open('x') as stream:
        json.dump(receipt, stream, indent=2)
        stream.write('\n')
    return receipt, path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    auth = parser.add_mutually_exclusive_group()
    auth.add_argument('--ambient-credentials', action='store_true')
    auth.add_argument('--profile')
    parser.add_argument('--output', type=Path, help='New directory for the discovery receipt')
    args = parser.parse_args()
    credentials = ['--ambient-credentials'] if args.ambient_credentials else (
        ['--profile', args.profile] if args.profile else [])
    label = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex
    destination = args.output or ROOT / '.work/storage/startup' / label
    receipt, path = startup(destination, credentials)
    print(json.dumps({'ready': receipt['ready'], 'receipt': str(path),
                      'bucket': receipt['bucket'], 'catalog_pointer': receipt['catalog_pointer']}))
    return 0 if receipt['ready'] else 1


if __name__ == '__main__':
    sys.exit(main())
