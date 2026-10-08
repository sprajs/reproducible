#!/usr/bin/env python3
"""Restore exact private-preservation versions to a new directory. No execution."""
import argparse, hashlib, json, os, re, shutil, subprocess, tarfile, tempfile
from pathlib import Path, PurePosixPath

def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def check_identity(profile):
    args=['aws','sts','get-caller-identity','--region','eu-west-2','--no-cli-pager','--output','json']
    if profile:args+=['--profile',profile]
    result=subprocess.run(args,capture_output=True,text=True,timeout=60)
    if result.returncode:raise RuntimeError('restricted identity unavailable')
    identity=json.loads(result.stdout)
    if identity['Account']!='436908790672' or identity['Arn'].endswith(':root'):
        raise ValueError('restricted configured research identity required')

def safe(name):
    if not isinstance(name,str) or not name or any(ord(c)<32 for c in name) or '\\' in name or name.startswith('/') or any(x in {'','.','..'} for x in name.split('/')):raise ValueError('unsafe path')
    return PurePosixPath(name)

def fetch(uri,version,dest,sha,size,profile):
    if not uri.startswith('s3://') or not version or version=='null' or not re.fullmatch('[0-9a-f]{64}',sha):raise ValueError('exact identity required')
    bucket,key=uri[5:].split('/',1);safe(key)
    if bucket!='research-data-436908790672-eu-west-2':raise ValueError('unconfigured bucket')
    args=['aws','s3api','get-object','--bucket',bucket,'--key',key,'--version-id',version,
        '--checksum-mode','ENABLED','--region','eu-west-2','--no-cli-pager','--output','json',str(dest)]
    if profile:args+=['--profile',profile]
    p=subprocess.run(args,capture_output=True,text=True,timeout=3600)
    if p.returncode:raise RuntimeError('exact version download failed')
    response=json.loads(p.stdout)
    if response.get('VersionId')!=version or digest(dest)!=sha or size is not None and dest.stat().st_size!=size:raise ValueError('download identity mismatch')

def recover(base,m):
    targets={}
    for e in m['entries']:
        if not e.get('upload'):continue
        u=e['upload'];safe(u['bundle']);safe(u['member']);safe(e['root_id']);safe(e['path'])
        entries=targets.setdefault((u['bundle'],u['member']),[])
        if entries and (entries[0]['sha256'],entries[0]['bytes'])!=(e['sha256'],e['bytes']):
            raise ValueError('conflicting deduplicated identity')
        entries.append(e)
    seen=set()
    for o in m['objects']:
        if o['kind']!='bundle':continue
        safe(o['path'])
        with tarfile.open(base/o['path'],'r:gz') as tf:
            for member in tf:
                key=(o['path'],member.name)
                if not member.isfile() or key not in targets or key in seen:raise ValueError('unsafe bundle member')
                entries=targets[key];e=entries[0]
                with tempfile.TemporaryDirectory(dir=base) as td:
                    blob=Path(td)/'blob'
                    with blob.open('xb') as f:shutil.copyfileobj(tf.extractfile(member),f)
                    if digest(blob)!=e['sha256'] or blob.stat().st_size!=e['bytes']:raise ValueError('member identity mismatch')
                    for e in entries:
                        dest=base/'recovered'/e['root_id']/e['path'];dest.parent.mkdir(parents=True,exist_ok=True)
                        with dest.open('xb') as f,blob.open('rb') as source:shutil.copyfileobj(source,f)
                seen.add(key)
    if seen!=set(targets):raise ValueError('missing recovery members')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--manifest-uri',required=True);ap.add_argument('--manifest-sha256',required=True);ap.add_argument('--manifest-version-id',required=True)
    ap.add_argument('--destination',type=Path,required=True);ap.add_argument('--profile',default='research');ap.add_argument('--ambient-credentials',action='store_true')
    ap.add_argument('--recover-roots',action='store_true',help='copy selected original occurrences under recovered/rootNN; no source execution')
    a=ap.parse_args();profile=None if a.ambient_credentials else a.profile
    if a.destination.exists() or a.destination.is_symlink():raise ValueError('destination must be new')
    check_identity(profile)
    with tempfile.TemporaryDirectory() as td:
        marker=Path(td)/'manifest.json';fetch(a.manifest_uri,a.manifest_version_id,marker,a.manifest_sha256,None,profile)
        doc=json.loads(marker.read_text())
        if doc['schema']!='research-private-preservation-transport/v1':raise ValueError('unknown manifest format')
        rows=doc['files'];names=[str(safe(r['path'])) for r in rows]
        if len(set(names))!=len(names) or 'manifest.json' not in names:raise ValueError('invalid file listing')
        a.destination.mkdir(parents=True,exist_ok=False)
        for r in rows:
            dest=a.destination/r['path'];dest.parent.mkdir(parents=True,exist_ok=True)
            fetch(r['uri'],r['version_id'],dest,r['sha256'],r['bytes'],profile)
        shutil.copyfile(marker,a.destination/'transport-manifest.json')
    m=json.loads((a.destination/'manifest.json').read_text())
    if digest(a.destination/'manifest.json')!=doc['classification_manifest_sha256']:raise ValueError('classification identity differs')
    if a.recover_roots:recover(a.destination,m)
    print(json.dumps({'verified_files':len(rows),'destination':str(a.destination),'recovered_originals':a.recover_roots,'git_and_redownload_routes':'manifest.json and audit/manifest-entries.jsonl.gz'}))

if __name__=='__main__':
    try:main()
    except Exception as e:raise SystemExit('Restore refused/failed: '+type(e).__name__+'; partial destination retained')
