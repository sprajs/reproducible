#!/usr/bin/env python3
"""Acquire exact declared family inputs; preserve partial attempts and refuse changed bytes.

Consumes a locally exact-version-verified research-resource/v1 family ledger.
The deadline is checked between reads; each network read may take up to45 seconds.
At an exactly exhausted transfer budget, exact frozen file length/hash may pass
without an additional upstream EOF probe; the receipt records that distinction.
Acquisition is separate from S3 publication, scientific admission and redistribution.
"""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request
import re
import time

from research_storage import safe, strict_json


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def acquire(asset, output, max_bytes, transfer_budget, max_attempts=4, deadline_seconds=180):
    size, sha = asset.get('expected_bytes'), asset.get('sha256')
    if type(size) is not int or size < 0 or size > max_bytes or not isinstance(sha, str) or not re.fullmatch(r'[0-9a-f]{64}', sha):
        return {'status': 'blocked', 'reason': 'missing exact identity or byte budget exceeded'}
    urls = list(dict.fromkeys(url for route in asset.get('acquisition_routes', [])
                             if route.get('kind') == 'pinned_download' for url in route.get('urls', [])))
    if not urls:
        return {'status': 'blocked', 'reason': 'no pinned upstream download route; inspect authoritative payload recovery'}
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise ValueError('fresh destination required')
    attempts = []
    received = 0
    deadline = time.monotonic() + deadline_seconds
    for index, url in enumerate(urls[:max_attempts]):
        if time.monotonic() >= deadline or transfer_budget <= received:
            attempts.append({'status': 'refused', 'reason': 'transfer/deadline budget exhausted'})
            break
        if not url.startswith('https://'):
            attempts.append({'url': url, 'status': 'refused', 'reason': 'HTTPS required'})
            continue
        partial = output.with_name(output.name + f'.attempt-{index}.partial')
        try:
            count = 0
            eof_checked = False
            request = urllib.request.Request(url, headers={'User-Agent': 'Reproducible-exact-input-acquisition/1'})
            with urllib.request.urlopen(request, timeout=45) as source, partial.open('xb') as stream:
                while True:
                    if time.monotonic() >= deadline or received >= transfer_budget:
                        raise ValueError('transfer/deadline budget exhausted')
                    block = source.read(min(1024 * 1024, size - count + 1, transfer_budget - received))
                    if not block:
                        eof_checked = True
                        break
                    received += len(block)
                    count += len(block)
                    stream.write(block)
                    if count > size:
                        raise ValueError('response exceeds declared byte count')
                    if count == size and received == transfer_budget:
                        # Exact input identity can be verified without spending
                        # an extra transfer byte beyond the declared cap.
                        break
            if count != size or digest(partial) != sha:
                raise ValueError('response differs from declared length/SHA256')
            # Link creates the admitted file without replacing another process's file.
            output.hardlink_to(partial)
            partial.unlink()
            attempts.append({'url': url, 'status': 'verified'})
            return {'status': 'acquired_exact_upstream', 'bytes': size, 'sha256': sha,
                    'path': str(output), 'attempts': attempts, 'received_bytes': received, 'upstream_eof_checked': eof_checked, 's3_payload_custody': False}
        except (Exception, KeyboardInterrupt) as exc:
            attempts.append({'url': url, 'status': 'failed', 'error': type(exc).__name__ + ': ' + str(exc)[:256],
                             'partial_path': str(partial) if partial.exists() else None,
                             'partial_bytes': partial.stat().st_size if partial.exists() else 0,
                             'partial_sha256': digest(partial) if partial.exists() else None})
            if isinstance(exc, KeyboardInterrupt):
                return {'status': 'interrupted', 'attempts': attempts, 'received_bytes': received, 's3_payload_custody': False}
    return {'status': 'failed', 'attempts': attempts, 'received_bytes': received, 's3_payload_custody': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--family-ledger', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--family', action='append')
    parser.add_argument('--max-asset-bytes', type=int, default=128 * 1024**2)
    parser.add_argument('--max-total-bytes', type=int, default=512 * 1024**2)
    args = parser.parse_args()
    if args.max_asset_bytes <= 0 or args.max_total_bytes <= 0:
        parser.error('positive byte budgets required')
    if args.destination.exists() or args.destination.is_symlink():
        parser.error('destination must be fresh')
    ledger = strict_json(args.family_ledger.read_text())
    args.destination.mkdir(parents=True)
    report = {'schema': 'dataset-acquisition-attempt/v1', 'catalog_pin': ledger['catalog_pin'],
              'family_ledger_sha256': digest(args.family_ledger), 'max_asset_bytes': args.max_asset_bytes,
              'max_total_bytes': args.max_total_bytes, 'assets': [],
              'deadline_policy': 'soft180s inter-read deadline, network reads timeout45s', 'scientific_admission': 'not_performed',
              'rights': 'private preservation source review required; no redistribution claim'}
    consumed = 0
    acquired = 0
    def checkpoint():
        (args.destination / 'acquisition.json').write_text(json.dumps(report, indent=2) + '\n')
    checkpoint()
    for family in ledger['families']:
        name = safe(family['catalog_entry']['name'])
        if args.family and name not in args.family:
            continue
        if family.get('metadata_fetch') != 'exact_version_verified':
            report['assets'].append({'family': name, 'status': 'blocked', 'reason': 'manifest not exact-version verified'})
            checkpoint()
            continue
        manifest = family['manifest']
        if manifest.get('schema') != 'research-resource/v1':
            raise ValueError('unsupported source manifest format')
        for index, asset in enumerate(manifest.get('assets', [])):
            size = asset.get('expected_bytes')
            result = {'family': name, 'asset_id': asset['id'], 'asset_class': asset.get('asset_class'),
                      'source_manifest': family['catalog_entry']['manifest'], 'semantics': manifest.get('semantics')}
            if type(size) is not int or size < 0:
                result.update(status='blocked', reason='invalid exact byte identity')
            elif consumed + size > args.max_total_bytes:
                result.update(status='blocked', reason='total declared acquisition byte budget exceeded')
            else:
                # Stable indexed names confine even historical asset identifiers containing .work paths.
                result.update(acquire(asset, args.destination / name / f'{index:03d}-{Path(asset["id"]).name}', args.max_asset_bytes, args.max_total_bytes - consumed))
                consumed += result.get('received_bytes', 0)
                if result['status'] == 'acquired_exact_upstream':
                    acquired += size
            report['assets'].append(result)
            report['acquired_bytes'] = acquired
            report['received_bytes_including_failed_attempts'] = consumed
            checkpoint()
            print(name, asset['id'], result['status'], flush=True)
            if result['status'] == 'interrupted':
                raise SystemExit(130)
    checkpoint()


if __name__ == '__main__':
    main()
