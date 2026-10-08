"""Acquire immutable reference sources and build one serial local runtime.

No scientific acceptance is implied by a build. All artifacts/logs stay in a
fresh ignored root. Existing roots are refused; failed attempts are preserved.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import subprocess
import sys
import tarfile
import time
import urllib.request

CLASS_REVISION = '0ceb7a9a4c1e444ef5d5d56a8328a0640be91b18'
SDK_REVISION = '7a006f81a36a70cdcd3187a1298a8a1ea2cf3f39'
CLASS_ARCHIVE = ('https://codeload.github.com/lesgourg/class_public/tar.gz/' + CLASS_REVISION,
                 '443a8b7c38b84cc8cfbb0dec907f1b618199e79df8d141dc3237b9a5185fb856', 20000000)
SDK_ARCHIVE = ('https://codeload.github.com/sprajs/irreducible/tar.gz/' + SDK_REVISION,
               '05e74c2c7802fdb6808e1fd8d887e0445fc76a447e94634e83def4b6925273cd', 20000000)
PLC_ARCHIVE = ('https://pla.esac.esa.int/pla/aio/product-action?COSMOLOGY.FILE_ID=COM_Likelihood_Code-v3.0_R3.01.tar.gz',
               'ea641f7ba6a1cdc6b6271079b2bb70613944260e7de57d53fee2516b77d68c8d', 20000000)
# Only a local Debian13 x86_64 compiler/header bootstrap; no system mutation.
DEBS = [
 ('pool/main/g/gcc-14/gfortran-14-x86-64-linux-gnu_14.2.0-19_amd64.deb', '520b3283edc193b75644d655654834662f56f9006a78751d91feb882b74ca684'),
 ('pool/main/g/gcc-14/libgfortran-14-dev_14.2.0-19_amd64.deb', '8460dfd941d9f60e92516e5c4e3f8bb08e60983e7526f376a7c87969a8a2dbfb'),
 ('pool/main/c/cfitsio/libcfitsio-dev_4.6.2-2_amd64.deb', '088cca05c0d3ae04c4829395c41eb2ffa1e2111a497cd918d57bd29af82170ff')]


def pin(path):
    path = Path(path).absolute()
    if not path.is_file() or path.is_symlink():
        raise ValueError('expected regular nonsymlink file')
    digest, size = hashlib.sha256(), 0
    with path.open('rb') as stream:
        for raw in iter(lambda: stream.read(1048576), b''):
            size += len(raw); digest.update(raw)
    return {'path': str(path), 'bytes': size, 'sha256': digest.hexdigest()}


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')
    return pin(path)


def download(path, spec):
    url, digest, limit = spec
    with urllib.request.urlopen(url, timeout=60) as response, Path(path).open('xb') as stream:
        total = 0
        while True:
            raw = response.read(1048576)
            if not raw:
                break
            total += len(raw)
            if total > limit:
                raise ValueError('download size ceiling')
            stream.write(raw)
    identity = pin(path)
    if identity['sha256'] != digest:
        raise ValueError('download SHA256 differs from frozen source')
    return {'url': url, **identity}


def extract(archive, dest, selected=None):
    """Reject traversal, links, duplicates and unsupported members before writes."""
    with tarfile.open(archive, 'r:*') as bundle:
        members, seen, total = [], set(), 0
        for member in bundle:
            name = Path(member.name)
            if name.is_absolute() or '..' in name.parts or member.name in seen:
                raise ValueError('unsafe or duplicate archive member')
            seen.add(member.name)
            if not (member.isdir() or member.isfile()):
                raise ValueError('archive links/special files refused')
            if selected is not None and not any(member.name == p or member.name.startswith(p + '/') for p in selected):
                continue
            total += member.size
            if len(members) >= 50000 or total > 4000000000 or member.size > 1000000000:
                raise ValueError('archive extraction ceiling')
            members.append(member)
        Path(dest).mkdir()
        for member in members:
            target = Path(dest) / member.name
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with bundle.extractfile(member) as source, target.open('xb') as output:
                    shutil.copyfileobj(source, output)
                target.chmod(member.mode & 0o777)


def inventory(root):
    return [pin(p) for p in sorted(Path(root).rglob('*')) if p.is_file() and not p.is_symlink()]


def source_manifest(root, revision, output):
    rows = inventory(root)
    if len(rows) > 512 or sum(p['bytes'] for p in rows) > 67108864:
        raise ValueError('source manifest bounds')
    for row in rows:
        row['path'] = str(Path(row['path']).relative_to(root))
    return write(output, {'source_revision': revision, 'source_root': str(root), 'source_files': rows})


class Builder:
    def __init__(self, root):
        self.root, self.commands = root, []
        self.deadline = time.monotonic() + 1800
        self.env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1')

    def run(self, command, cwd=None, timeout=900):
        log = self.root / ('command-%03d.log' % len(self.commands))
        row = {'argv': list(map(str, command)), 'cwd': str(cwd or self.root), 'log': str(log), 'started_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'single_thread_environment': {k: self.env[k] for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS')}}
        self.commands.append(row)
        write(self.root / ('command-%03d.json' % (len(self.commands)-1)), row)
        with log.open('xb') as stream:
            process = subprocess.Popen(row['argv'], cwd=cwd or self.root, env=self.env, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
            try:
                code = process.wait(timeout=min(timeout, max(0.001, self.deadline - time.monotonic())))
            except BaseException:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                except OSError as cleanup:
                    row['cleanup_error'] = str(cleanup)[:512]
                process.wait(timeout=10)
                row.update(returncode=process.returncode, log_identity=pin(log), interrupted=True)
                raise
        row.update(returncode=code, log_identity=pin(log))
        if code:
            raise ValueError('build failed: ' + log.name)

    def receipt(self, name, sources, artifacts):
        return write(self.root / (name + '-build.json'), {'schema': 'cosmology-runtime-build/v1', 'source_identities': sources, 'commands': self.commands[:], 'artifacts': artifacts, 'platform': platform.platform(), 'python': pin(Path(sys.executable).resolve()), 'build_tools': self.tool_identities(), 'scientific_acceptance': None})


    def tool_identities(self):
        paths = {str(Path(row['argv'][0]).resolve()) for row in self.commands}
        paths.update(executable(name) for name in ('cc', 'c++', 'ld', 'ar'))
        result = []
        for path in sorted(paths):
            version = subprocess.run([path, '--version'], capture_output=True, text=True, timeout=10)
            result.append({'identity': pin(path), 'version': version.stdout[:4096], 'returncode': version.returncode})
        return result


def dynamic_dependencies(binary):
    result = subprocess.run([executable('ldd'), str(binary)], capture_output=True, text=True, timeout=10, check=True)
    dependencies = []
    for line in result.stdout.splitlines():
        fields = line.split()
        if 'not found' in line:
            raise ValueError('unresolved dynamic dependency')
        path = fields[2] if len(fields) >= 3 and fields[1] == '=>' else fields[0] if fields and fields[0].startswith('/') else None
        if path and Path(path).is_file():
            identity = pin(Path(path).resolve())
            if identity not in dependencies:
                dependencies.append(identity)
    return dependencies


def executable(name):
    path = shutil.which(name)
    if path is None:
        raise ValueError('required build tool missing: ' + name)
    return str(Path(path).resolve())


def library(name):
    value = subprocess.check_output([executable('cc'), '-print-file-name=' + name], text=True).strip()
    if value == name:
        raise ValueError('required shared runtime missing: ' + name)
    return str(Path(value).resolve(strict=True))


def bootstrap(root, skip_planck=False, cmake=None):
    root = Path(root)
    if not root.is_absolute() or '..' in root.parts or root.exists() or any(p.is_symlink() for p in root.parents):
        raise ValueError('require fresh absolute runtime root without symlinks')
    repo = Path(__file__).resolve().parents[1]
    if not root.is_relative_to(repo / '.work'):
        raise ValueError('runtime root must be under repository ignored .work')
    root.mkdir(parents=True)
    builder, archives = Builder(root), []
    try:
        script_identity = pin(Path(__file__).resolve())
        snapshot = root / 'bootstrap-source.py'
        snapshot.write_bytes(Path(__file__).read_bytes())
        if pin(snapshot)['sha256'] != script_identity['sha256']:
            raise ValueError('bootstrap source changed during snapshot')
        for name, spec in [('class', CLASS_ARCHIVE), ('sdk', SDK_ARCHIVE)]:
            archive = root / (name + '.tar.gz')
            archives.append(download(archive, spec)); extract(archive, root / name)
        class_src = root / 'class' / ('class_public-' + CLASS_REVISION)
        sdk_src = root / 'sdk' / ('irreducible-' + SDK_REVISION)
        class_manifest = source_manifest(class_src, CLASS_REVISION, root / 'class-source.json')
        sdk_sources = inventory(sdk_src)
        cmake = str(Path(cmake).resolve(strict=True)) if cmake else executable('cmake')
        builder.run([cmake, '-S', sdk_src / 'cpp', '-B', root / 'sdk-build', '-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_INSTALL_PREFIX=' + str(root / 'sdk-install')])
        builder.run([cmake, '--build', root / 'sdk-build', '--target', 'irred_core', '--parallel', '1'])
        builder.run([cmake, '--install', root / 'sdk-build'])
        sdk_files = inventory(root / 'sdk-install')
        build_id = hashlib.sha256(json.dumps({'source_revision': SDK_REVISION, 'files': [{k:v for k,v in r.items() if k != 'path'} for r in sdk_files]}, sort_keys=True).encode()).hexdigest()
        consumer = repo / 'experiments/lcdm-bao-reference/consumer.cpp'
        binary = root / 'gaussian-consumer'
        builder.run([executable('c++'), '-std=c++20', '-O2', '-fno-fast-math', '-ffp-contract=off', '-DIRRED_CLASS_BAO_BUILD_ID="' + build_id + '"', '-I' + str(root / 'sdk-install/include'), consumer, root / 'sdk-install/lib/libirred_core.a', '-o', binary])
        sdk_files += dynamic_dependencies(binary)
        gaussian = {'binary': pin(binary), 'sdk_build_id': build_id, 'source_revision': SDK_REVISION, 'consumer_source': pin(consumer), 'sdk_inventory': sdk_files, 'build_receipt': builder.receipt('gaussian', sdk_sources + [pin(consumer)], [pin(binary)] + sdk_files)}
        builder.run([executable('make'), '-j1', 'class'], cwd=class_src)
        class_binary = pin(class_src / 'class')
        class_dependencies = dynamic_dependencies(class_src / 'class')
        engine = {'revision': CLASS_REVISION, 'source_root': str(class_src), 'source_manifest': class_manifest, 'binary': class_binary, 'build_receipt': builder.receipt('class', [class_manifest], [class_binary] + class_dependencies)}
        planck = None if skip_planck else build_planck(builder, archives)
        if pin(Path(__file__).resolve()) != script_identity:
            raise ValueError('bootstrap source changed during build')
        runtime = {'bootstrap_source': script_identity, 'bootstrap_snapshot': pin(snapshot), 'schema': 'observational-cosmology-runtime/v1', 'class': engine, 'gaussian': gaussian, 'planck': planck, 'archives': archives, 'class_dependencies': class_dependencies}
        write(root / 'runtime.json', runtime)
        return runtime
    except BaseException as exc:
        write(root / 'failure.json', {'status': 'failed', 'error_type': type(exc).__name__, 'message': str(exc)[:2048], 'commands': builder.commands, 'archives': archives})
        raise


PLANCK_DATA = ('https://pla.esac.esa.int/pla/aio/product-action?COSMOLOGY.FILE_ID=COM_Likelihood_Data-baseline_R3.00.tar.gz',
               '0b73171e3acc671c28184466a45485a2d1c1d93676b832abdfe688c7b04024e6', 100000000)
PRODUCTS = ['low_l/commander/commander_dx12_v3_2_29.clik',
            'low_l/simall/simall_100x143_offlike5_EE_Aplanck_B.clik',
            'hi_l/plik_lite/plik_lite_v22_TTTEEE.clik']


def build_planck(builder, archives):
    root = builder.root
    archive = root / 'plc.tar.gz'
    archives.append(download(archive, PLC_ARCHIVE)); extract(archive, root / 'plc')
    source = root / 'plc/code/plc_3.0/plc-3.01'
    source_files = inventory(source)
    data = root / 'planck-baseline.tar.gz'
    archives.append(download(data, PLANCK_DATA))
    extract(data, root / 'planck-data', ['baseline/plc_3.0/' + p for p in PRODUCTS])
    plc_root = root / 'planck-data/baseline/plc_3.0'
    tools = root / 'tools'
    tools.mkdir()
    compiler = shutil.which('gfortran') or shutil.which('gfortran-14')
    headers = Path('/usr/include')
    if compiler is None or not (headers / 'fitsio.h').is_file():
        if platform.system() != 'Linux' or platform.machine() != 'x86_64' or 'VERSION_ID="13"' not in Path('/etc/os-release').read_text():
            raise ValueError('install gfortran and CFITSIO development headers; local fallback supports Debian13 x86_64')
        for relative, digest in DEBS:
            package = tools / Path(relative).name
            archives.append(download(package, ('https://deb.debian.org/debian/' + relative, digest, 20000000)))
            builder.run([executable('dpkg-deb'), '-x', package, tools / 'install'])
        if compiler is None:
            compiler = str(tools / 'install/usr/bin/x86_64-linux-gnu-gfortran-14')
        headers = tools / 'install/usr/include'
    build = root / 'plc-build'
    build.mkdir()
    c_sources = ['minipmc/errorlist.c', 'minipmc/io.c', 'minipmc/distribution.c',
                 'cldf/cldf.c', 'cldf/cfrd.c', 'clik_dic.c', 'clik.c', 'lklbs.c',
                 'lowly_common.c', 'clik_helper.c', 'gibbs/clik_gibbs.c',
                 'cmbonly/clik_cmbonly.c', 'simall/clik_simall.c']
    f_sources = ['gibbs/comm_br_mod.f90', 'gibbs/comm_gauss_br_mod.f90',
                 'gibbs/comm_gauss_br_mod_v3.f90', 'gibbs/comm_lowl_mod_dist.f90',
                 'gibbs/clik_gibbs.f90', 'cmbonly/plik_cmbonly.f90',
                 'cmbonly/clik_cmbonly.f90']
    objects = []
    includes = ['-I' + str(source / 'src' / p) for p in ('', 'minipmc', 'cldf', 'plik')]
    includes += ['-I' + str(headers)]
    for item in c_sources:
        output = build / (Path(item).name + '.o'); objects.append(output)
        builder.run([executable('cc'), '-O2', '-fPIC', '-DHAS_LAPACK', '-DLAPACK_CLIK', '-DNOHEALPIX', '-DHAS_RTLD_DEFAULT', '-DCLIKSVNVERSION="PLC_3.01-selected-official-sources"', *includes, '-c', source / 'src' / item, '-o', output], cwd=build)
    for item in f_sources:
        output = build / (Path(item).name + '.o'); objects.append(output)
        builder.run([compiler, '-O2', '-fPIC', '-ffree-line-length-0', '-J' + str(build), '-c', source / 'src' / item, '-o', output], cwd=build)
    output = build / 'libclik.so'
    builder.run([executable('cc'), '-shared', '-Wl,-z,defs', '-o', output, *objects, library('liblapack.so.3'), library('libblas.so.3'), library('libcfitsio.so.10'), library('libgfortran.so.5'), '-ldl', '-lm', '-lpthread'])
    # Record complete resolved dynamic dependencies; their original files are
    # admitted in the runtime, rather than falsely labelling them source-pinned.
    dependencies = dynamic_dependencies(output)
    admission = source_files + inventory(plc_root) + dependencies
    receipt = builder.receipt('plc', source_files, [pin(output)] + dependencies)
    return {'plc_root': str(plc_root), 'library': pin(output), 'admission_files': admission,
            'build_receipt': receipt, 'archives': archives[-5:],
            'selected_products': PRODUCTS, 'dependency_libraries': dependencies,
            'build_scope': 'official selected Commander/SimAll/Plik-lite C API; no likelihood source changes'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--skip-planck', action='store_true')
    parser.add_argument('--cmake', help='absolute installed CMake >=3.24 executable')
    args = parser.parse_args()
    bootstrap(args.root, args.skip_planck, args.cmake)
    print(str(Path(args.root) / 'runtime.json'))


if __name__ == '__main__':
    main()
