"""Bounded production SDK campaign; Python implements no physical equations."""
import argparse
import datetime
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
FOLDER = Path(__file__).resolve().parent
COMMON = ROOT / 'experiments/native-model-campaign/controller.py'
spec = importlib.util.spec_from_file_location('native_campaign_admission', COMMON)
admission = importlib.util.module_from_spec(spec)
spec.loader.exec_module(admission)
require, pin, write = admission.require, admission.pin, admission.write
CG_METRICS = {'E', 'H_km_s_Mpc', 'rho_fluid_over_anchor', 'Omega_ordinary', 'Omega_radiation', 'Omega_fluid', 'w_fluid', 'one_plus_w_fluid', 'formal_dp_de', 'w_total', 'deceleration', 'DC_Mpc', 'DA_Mpc', 'DL_Mpc'}
RADIUS_METRICS = {'density_kg_m3', 'Psi_m2_s2', 'enclosed_mass_kg', 'projected_surface_density_kg_m2', 'escape_speed_m_s', 'one_axis_variance_m2_s2', 'projected_los_variance_m2_s2'}
VELOCITY_METRICS = {'DF_kg_s3_m6', 'vector_PDF_s3_m3', 'speed_PDF_s_m'}


def strict_json(raw):
    value = admission.strict_json(raw)
    def finite(item):
        if isinstance(item, float):
            require(math.isfinite(item), 'nonfinite JSON numeric literal')
        elif isinstance(item, list):
            for child in item:
                finite(child)
        elif isinstance(item, dict):
            for child in item.values():
                finite(child)
    finite(value)
    return value


def expected_states(request):
    cg = request['parameters']['chaplygin']
    pop = request['parameters']['plummer_population']
    states = {}
    for i, (a_s, alpha) in enumerate(itertools.product(cg['a_s'], cg['alpha'])):
        states['chaplygin', i] = {**{k: v for k, v in cg.items() if k not in ('a_s', 'alpha')}, 'a_s': a_s, 'alpha': alpha}
    for i, (mass, scale) in enumerate(itertools.product(pop['M_kg'], pop['b_m'])):
        states['plummer_population', i] = {'M_kg': mass, 'b_m': scale, 'supplied_G_m3_kg_s2': pop['supplied_G_m3_kg_s2']}
    return states


def qualify(report, request, profile, request_sha):
    require(report['schema'] == 'compiled-native-fluid-population/v1' and report['profile'] == profile and report['build_id'] == request['sdk_pin']['build_id'] and report['request_sha256'] == request_sha, 'native identity differs')
    require(report['observations'] is None and report['inference'] is None, 'synthetic role changed')
    require(len(report['cases']) == request['expected_cases'], 'case count differs')
    states, grouped = expected_states(request), {}
    axes, gate = request['coordinates'][profile], request['numerical_gate']
    boundary = request['boundary_control']['q']
    total_rows = total_radii = 0
    comparisons, failures, boundary_rows = [], [], []
    for case in report['cases']:
        key = case['family'], case['id']
        require(key in states and case['parameters'] == states[key], 'physical parameter binding differs')
        require(case['model_id'] == request['model_ids'][case['family']], 'native physical model differs')
        require(case['resolution'] in ('default', 'refined') and case['resolution'] not in grouped.setdefault(key, {}), 'duplicate/unsupported case resolution')
        grouped[key][case['resolution']] = case
        total_rows += len(case['rows'])
        if key[0] == 'chaplygin':
            require([r['coordinate'] for r in case['rows']] == axes['a'], 'GCG coordinate coverage differs')
            require(all(set(r['values']) == CG_METRICS for r in case['rows']), 'GCG response fields differ')
        else:
            expected_axes = [{'radius_index': i, 'radius_over_scale': radius, 'speed_over_native_escape': q} for i, radius in enumerate(axes['radius_over_scale']) for q in axes['speed_over_native_escape']]
            require([r['coordinate'] for r in case['rows']] == expected_axes, 'velocity coordinate coverage differs')
            require([r['coordinate'] for r in case['radius_states']] == axes['radius_over_scale'], 'radius coverage differs')
            require(all(set(r['values']) == RADIUS_METRICS for r in case['radius_states']) and all(set(r['values']) == VELOCITY_METRICS for r in case['rows']), 'population response fields differ')
            total_radii += len(case['radius_states'])
    require(set(grouped) == set(states) and total_rows == request['expected_rows'][profile] and total_radii == request['expected_radius_states'][profile], 'complete physical selection differs')

    def compare(key, label, first, second):
        require(first['coordinate'] == second['coordinate'] and set(first['values']) == set(second['values']), 'policy comparison axes differ')
        for metric, x in first['values'].items():
            y = second['values'][metric]
            if x['status'] != 0 or y['status'] != 0:
                failures.append({'family': key[0], 'case': key[1], 'coordinate': first['coordinate'], 'metric': metric, 'cause': 'native refusal', 'default': x, 'refined': y})
                continue
            require(type(x['value']) in (int, float) and type(y['value']) in (int, float), 'missing admitted finite output')
            absolute = abs(x['value'] - y['value'])
            scale = max(abs(x['value']), abs(y['value']))
            allowance = gate['relative_difference'] * scale
            if metric in ('w_fluid', 'one_plus_w_fluid', 'formal_dp_de', 'w_total'):
                allowance = gate['absolute_w_and_barotropic_slope']
            elif metric.endswith('_Mpc'):
                allowance += gate['distance_absolute_mpc']
            elif not scale:
                allowance = gate['exact_zero_absolute_floor']
            item = {'family': key[0], 'case': key[1], 'section': label, 'coordinate': first['coordinate'], 'metric': metric, 'absolute_difference': absolute, 'allowance': allowance, 'passed': absolute <= allowance}
            comparisons.append(item)
            if not item['passed']:
                failures.append(item)

    for key, pair in grouped.items():
        require(set(pair) == {'default', 'refined'}, 'missing policy comparison partner')
        first, second = pair['default'], pair['refined']
        for a, b in zip(first.get('radius_states', []), second.get('radius_states', [])):
            compare(key, 'radius', a, b)
        for a, b in zip(first['rows'], second['rows']):
            if key[0] == 'plummer_population' and a['coordinate']['speed_over_native_escape'] == boundary:
                contracts = []
                for resolution, row in (('default', a), ('refined', b)):
                    energy, error = row['binding_energy_m2_s2'], row['binding_energy_absolute_error_m2_s2']
                    lower, upper = energy - error, energy + error
                    if lower > 0:
                        valid = row['support'] == 1 and row['native_status'] == 0 and all(v['status'] == 0 and v['value'] is not None for v in row['values'].values())
                    elif upper <= 0:
                        valid = row['support'] == 2 and row['native_status'] == 0 and all(v['status'] == 0 and v['value'] == 0 for v in row['values'].values())
                    else:
                        valid = row['support'] == 3 and row['native_status'] == 8 and all(v['status'] == 8 and v['value'] is None for v in row['values'].values())
                    contracts.append({'resolution': resolution, 'native_contract_passed': valid and error >= 0})
                    if not valid or error < 0:
                        failures.append({'cause': 'boundary native diagnostic contract inconsistent', 'case': key[1], 'coordinate': row['coordinate'], 'resolution': resolution})
                boundary_rows.append({'family': key[0], 'case': key[1], 'coordinate': a['coordinate'], 'default': a, 'refined': b, 'contracts': contracts, 'comparison': 'unassessed deliberate support boundary; empirical native diagnostics retained'})
                continue
            compare(key, 'prediction', a, b)
            if key[0] == 'plummer_population' and a['coordinate']['speed_over_native_escape'] > 1:
                for row in (a, b):
                    require(row['support'] == 2 and row['binding_energy_m2_s2'] + row['binding_energy_absolute_error_m2_s2'] <= 0, 'native outside-support diagnostic missing')
                    require(all(v['status'] == 0 and v['value'] == 0 for v in row['values'].values()), 'outside native exactzero withheld')
    expected_controls = {'compiled-FLRW-endpoint-' + str(i) for i in range(8)} | {'GCG-future-outside-domain-withheld', 'negative-speed-refused', 'native-outside-support-diagnostic-zero'}
    require(len(report['controls']) == len(expected_controls) and {x['id'] for x in report['controls']} == expected_controls, 'reference/refusal controls differ')
    for control in report['controls']:
        if control['passed'] is not True:
            failures.append({'cause': 'native control failed', 'control': control})
    return {'status': 'passed_on_admitted_grid_with_retained_boundary_diagnostics' if not failures else 'rejected_or_incomplete', 'comparisons': comparisons, 'failures': failures, 'boundary_rows': boundary_rows, 'certified_error_bound': None, 'independent_engine_reference_checks': 'separate pinned permanent native tests; not inferred from this policy comparison', 'observational_qualification': 'not_claimed', 'inference': 'not_performed'}


def execute(args):
    attempt = admission.clean_path(args.attempt)
    require(attempt.is_relative_to(ROOT / 'results') and not attempt.exists(), 'fresh ignored attempt required')
    attempt.parent.mkdir(parents=True, exist_ok=True)
    admission.clean_path(attempt.parent)
    attempt.mkdir(mode=0o700)
    record = {'schema': 'native-fluid-population-attempt/v1', 'status': 'failed', 'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'profile': args.profile, 'observations': None, 'inference': None, 'errors': []}
    try:
        request = strict_json((FOLDER / 'request.json').read_text())
        require(request['sdk_pin'] and request['engine_revision'], 'final production SDK identity pending')
        record['source_before'] = admission.source_state(ROOT)
        record['request'] = pin(FOLDER / 'request.json')
        record['sdk_before'] = admission.sdk_state(args.sdk, args.engine_source, args.build_manifest, request)
        for name in ('request.json', 'consumer.cpp', 'controller.py', 'experiment.json'):
            (attempt / name).write_bytes((FOLDER / name).read_bytes())
        (attempt / 'shared-admission-controller.py').write_bytes(COMMON.read_bytes())
        (attempt / 'build-manifest.snapshot.json').write_bytes(args.build_manifest.read_bytes())
        record['new_installed_headers'] = {name: pin(args.sdk / 'include/irred' / (name + '.hpp')) for name in ('chaplygin', 'plummer_population')}
        manifest = strict_json(args.build_manifest.read_text())
        for name, item in record['new_installed_headers'].items():
            require(item['sha256'] == manifest['sources']['cpp/include/irred/' + name + '.hpp'], 'new installed header differs from final source')
        compiler = Path(shutil.which('c++')).resolve(strict=True)
        record['compiler'] = {'identity': pin(compiler), 'version': subprocess.check_output([str(compiler), '--version'], text=True).splitlines()[0]}
        binary = attempt / 'native-consumer'
        command = [str(compiler), '-std=c++20', '-O2', '-Wall', '-Wextra', '-Wpedantic', '-Werror', '-fno-fast-math', '-ffp-contract=off', '-DCAMPAIGN_BUILD_ID="' + request['sdk_pin']['build_id'] + '"', '-DCAMPAIGN_REQUEST_SHA="' + record['request']['sha256'] + '"', '-I', str(args.sdk / 'include'), str(FOLDER / 'consumer.cpp'), str(args.sdk / 'lib/libirred_core.a'), '-o', str(binary)]
        record['compile'] = admission.run_process(command, attempt, request['limits'], 'compile')
        record['binary'] = pin(binary)
        record['execution'] = admission.run_process([str(binary), args.profile], attempt, request['limits'], 'native')
        record['numerical'] = qualify(strict_json((attempt / 'native.stdout').read_text()), request, args.profile, record['request']['sha256'])
        write(attempt / 'qualification.json', record['numerical'])
        record['sdk_after'] = admission.sdk_state(args.sdk, args.engine_source, args.build_manifest, request)
        record['source_after'] = admission.source_state(ROOT)
        require(record['sdk_before'] == record['sdk_after'] and record['source_before'] == record['source_after'], 'terminal source/SDK drift')
        record['status'] = 'completed'
    except Exception as error:
        record['errors'].append({'kind': type(error).__name__, 'message': str(error)[:2048]})
    finally:
        record['completed_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        record['files'] = [{**pin(p), 'relative_path': str(p.relative_to(attempt))} for p in sorted(attempt.rglob('*')) if p.is_file()]
        require(sum(x['bytes'] for x in record['files']) <= 33554432, 'attempt byte cap')
        write(attempt / 'manifest.json', record)
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('sdk', 'engine-source', 'build-manifest', 'attempt'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--profile', choices=('quick', 'broader'), default='quick')
    args = parser.parse_args()
    result = execute(args)
    print(json.dumps({'execution': result['status'], 'numerical': result.get('numerical', {}).get('status'), 'errors': result['errors']}))
    raise SystemExit(result['status'] != 'completed' or result['numerical']['failures'])
