"""Four independent transformed MH chains; emcee/SciPy own sampling kernels."""
import hashlib
import types
import json
import math
import os
from pathlib import Path
import sys


def execute_bound_source(expected, name, limit):
    source = Path(expected['path']).resolve()
    if source.is_symlink() or source.stat().st_size > limit:
        raise ValueError('bounded regular pinned source required')
    raw = source.read_bytes()
    if len(raw) != expected['bytes'] or hashlib.sha256(raw).hexdigest() != expected['sha256']:
        raise ValueError('executing source bytes differ from policy')
    module = types.ModuleType(name)
    module.__file__ = str(source)
    exec(compile(raw, str(source), 'exec'), module.__dict__)
    return module


# The controller binds these exact bytes before importing this orchestration.
# No source loader may choose a cached bytecode body instead.
coordinates = execute_bound_source(_ADMITTED_COORDINATES_PIN, 'relative_sn_coordinates', 16384)


def pin(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def atomic(path, value):
    raw = (json.dumps(value, sort_keys=True, allow_nan=False) + '\n').encode()
    pending = path.with_suffix(path.suffix + '.pending')
    with pending.open('wb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    os.replace(pending, path)
    return pin(path)


def admitted_engine(policy):
    expected = policy['reviewed_primary_engine_source']
    if pin(expected['path']) != expected:
        raise ValueError('reviewed statistical engine source identity differs')
    return execute_bound_source(expected, 'reviewed_primary_statistical_inventory', 1048576)


def run_chain(evaluator, configuration, attempt, engine_inventory):
    """Singleton MHMove: fixed independence t6 or fixed symmetric t6 pilot.

    The proposal densities are densities in u. The physical prior Jacobian is
    included by evaluator, once, and never in the Hastings proposal ratio.
    """
    import emcee
    import numpy as np
    import scipy
    from scipy.stats import multivariate_t
    location = np.asarray(configuration['proposal_location'], dtype=float)
    shape = np.asarray(configuration['proposal_shape'], dtype=float)
    if location.shape != (4,) or shape.shape != (4, 4) or not np.all(np.isfinite([*location, *shape.ravel()])):
        raise ValueError('finite four-dimensional frozen t6 geometry required')
    if not np.array_equal(shape, shape.T):
        raise ValueError('exact symmetric frozen proposal shape required')
    np.linalg.cholesky(shape)
    kind = configuration['proposal_kind']
    if kind not in ('independence_t6', 'symmetric_randomwalk_t6'):
        raise ValueError('closed external proposal choice required')
    law = multivariate_t(loc=location if kind == 'independence_t6' else np.zeros(4), shape=shape, df=6)
    seed = configuration['seed']
    if type(seed) is not int or not 0 <= seed < 2**32:
        raise ValueError('explicit independent seed required')
    if type(configuration['raw_steps']) is not int or configuration['raw_steps'] <= 0:
        raise ValueError('positive frozen raw transition count required')
    raw_count = 0
    proposals = (attempt / 'proposals.jsonl').open('x')
    states = (attempt / 'states.jsonl').open('x')
    def proposal(current, rng):
        vector = np.asarray(law.rvs(size=len(current), random_state=rng)).reshape(current.shape)
        if kind == 'independence_t6':
            ratio = np.atleast_1d(law.logpdf(current) - law.logpdf(vector))
        else:
            vector = current + vector
            ratio = np.zeros(len(current))  # The centered t6 increment is symmetric.
        proposals.write(json.dumps({'transition': raw_count+1, 'kind': kind,
            'u': vector[0].tolist(), 'log_reverse_over_forward': float(ratio[0])}, allow_nan=False)+'\n')
        proposals.flush()
        return vector, ratio
    def target(u):
        row = evaluator.score(u)
        if row['status'] == 'physical_prior_excluded':
            return -np.inf, {'physical_prior_excluded': True}
        return row['logtarget_u'], row
    sampler = emcee.EnsembleSampler(1, 4, target,
        moves=emcee.moves.MHMove(proposal, ndim=4), blobs_dtype=object)
    sampler.random_state = np.random.RandomState(seed).get_state()
    start = np.asarray(configuration['start_u'], dtype=float).reshape(1, 4)
    logp, blobs = sampler.compute_log_prob(start)
    if not np.all(np.isfinite(logp)):
        raise ValueError('finite explicit chain start required')
    state = emcee.State(start, log_prob=logp, blobs=blobs, random_state=sampler.random_state)
    kernel_pins = engine_inventory.kernel_inventory()
    inventory_pin = atomic(attempt / 'statistical-kernel-inventory.json', kernel_pins)
    configuration_pin = atomic(attempt / 'configuration.json', configuration)
    def checkpoint(phase):
        rng = state.random_state
        atomic(attempt / 'statistical-state.json', {'schema': 'sn-relative-singleton-mh-state/v1',
            'phase': phase, 'completed_transitions': raw_count, 'source': pin(__file__),
            'coordinates_source': pin(Path(__file__).with_name('coordinates.py')),
            'configuration_pin': configuration_pin, 'kernel_inventory_pin': inventory_pin,
            'versions': {'emcee': emcee.__version__, 'numpy': np.__version__, 'scipy': scipy.__version__},
            'coords': state.coords.tolist(), 'log_prob_u': state.log_prob.tolist(),
            'blobs': state.blobs.tolist(), 'random_state': [rng[0], rng[1].tolist(),
                int(rng[2]), int(rng[3]), float(rng[4])], 'evaluator_calls': evaluator.count})
    checkpoint('initialized')
    try:
        for state in sampler.sample(state, iterations=configuration['raw_steps'],
                                    store=False, skip_initial_state_check=True):
            raw_count += 1
            blob = state.blobs[0]
            if type(blob) is not dict or blob.get('status') != 'finite':
                raise ValueError('retained finite external state required')
            row = dict(blob)
            row.update(transition=raw_count, weight=1, u=state.coords[0].tolist(),
                       logtarget_u=float(state.log_prob[0]))
            states.write(json.dumps(row, sort_keys=True, allow_nan=False)+'\n'); states.flush()
            if raw_count % configuration['checkpoint_every'] == 0:
                os.fsync(states.fileno()); os.fsync(proposals.fileno()); checkpoint('running')
        checkpoint('completed')
        return {'status': 'completed', 'raw_transitions': raw_count,
            'seed': seed, 'evaluator_calls': evaluator.count,
            'single_walker_independent_chain': True, 'production_adaptation': False,
            'proposal_df': 6, 'proposal_shape_is_not_covariance': True,
            'proposal_covariance': (1.5*shape).tolist(), 'posterior_qualified': False}
    except BaseException as original_error:
        try:
            checkpoint('refused_or_interrupted')
        except BaseException as checkpoint_error:
            original_error.add_note('Failed prefix checkpoint also refused: '+str(checkpoint_error))
        raise
    finally:
        states.close(); proposals.close()
        original_error = sys.exception()
        try:
            engine_inventory.verify_kernel_inventory(kernel_pins)
        except BaseException as error:
            if original_error is not None:
                original_error.add_note('After-admission statistical closure refused: '+str(error))
            else:
                raise


class UniformPhysicalBoxControl:
    def __init__(self):
        self.count = 0
    def score(self, u):
        self.count += 1
        physical = coordinates.inverse(u)
        if physical is None:
            return {'status': 'physical_prior_excluded'}
        return {'status': 'finite', 'physical': dict(zip(coordinates.PHYSICAL, physical)),
            'loglike': 0.0, 'proper_logprior': coordinates.LOG_PRIOR,
            'logtarget_physical': coordinates.LOG_PRIOR,
            'log_jacobian': coordinates.log_jacobian(u),
            'logtarget_u': coordinates.LOG_PRIOR+coordinates.log_jacobian(u)}


def diagnose(paths, warmup, uniform_control=False):
    import arviz as az
    import numpy as np
    quantities = [*coordinates.PHYSICAL, 'Omega_cb', 'eta', 'calM', 'logtarget_u']
    if not uniform_control:
        quantities.append('logtarget_physical')
    traces = []
    for path in paths:
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        if any(row['weight'] != 1 for row in rows):
            raise ValueError('exact unit holding records required')
        traces.append([[*[row['physical'][n] for n in coordinates.PHYSICAL],
                        *row['u'][1:], row['logtarget_u'],
                        *([] if uniform_control else [row['logtarget_physical']])]
                       for row in rows[warmup:]])
    if len(traces) != 4 or len({len(t) for t in traces}) != 1:
        raise ValueError('four equal-length completed independent chains required')
    draws = np.asarray(traces, dtype=float)
    if not np.all(np.isfinite(draws)):
        raise ValueError('finite diagnostics draws required')
    data = az.from_dict(posterior={name: draws[:, :, i] for i, name in enumerate(quantities)})
    rh = az.rhat(data, method='rank').to_array().values
    bulk = az.ess(data, method='bulk').to_array().values
    tail = az.ess(data, method='tail').to_array().values
    mcse = az.mcse(data, method='mean').to_array().values
    sd = draws.std(axis=(0, 1), ddof=1)
    statistics = {name: {'rank_split_rhat': float(rh[i]), 'combined_bulk_ess': float(bulk[i]),
        'combined_tail_ess': float(tail[i]), 'mean_mcse': float(mcse[i]),
        'sd': float(sd[i]), 'mcse_over_sd': float(mcse[i]/sd[i])}
        for i, name in enumerate(quantities)}
    limits_pass = bool(np.all(np.isfinite([*rh, *bulk, *tail, *mcse, *sd]))
        and np.all(rh < 1.01) and np.all(bulk >= 400) and np.all(tail >= 400)
        and np.all(mcse/sd <= .05))
    boundary = {}
    for i, name in enumerate(coordinates.PHYSICAL):
        lo, hi = coordinates.BOUNDS[i]; width = hi-lo
        boundary[name] = {'central_95_interval': np.quantile(draws[:, :, i], [.025, .975]).tolist(),
            'lower_5pct_shell': float((draws[:, :, i] <= lo+.05*width).mean()),
            'upper_5pct_shell': float((draws[:, :, i] >= hi-.05*width).mean()),
            'interpretation': 'source box and SN-only ridge can control posterior tails; convergence does not establish prior robustness'}
    result = {'schema': 'sn-relative-four-chain-diagnostics/v1', 'statistics': statistics,
        'boundaries': boundary, 'raw_draws_per_chain_after_discard': len(traces[0]),
        'convergence_qualified': limits_pass, 'posterior_qualified': False}
    if uniform_control:
        means = np.asarray([.023, .13, 70., -19.])
        variances = np.asarray([.01**2, .10**2, 40.**2, 4.**2])/12
        moments = []
        for i, name in enumerate(coordinates.PHYSICAL):
            moments.append((name+'_mean', draws[:, :, i], means[i]))
            for j in range(i, 4):
                moments.append((name+'_'+coordinates.PHYSICAL[j]+'_knownmean_product',
                    (draws[:, :, i]-means[i])*(draws[:, :, j]-means[j]), variances[i] if i == j else 0.0))
        tests = []
        for name, samples, truth in moments:
            estimate = float(samples.mean())
            error = float(az.mcse(az.from_dict(posterior={'moment': samples}), method='mean').moment.values)
            z = abs(estimate-truth)/error if error > 0 else math.inf
            tests.append({'name': name, 'estimate': estimate, 'truth': float(truth),
                'autocorrelation_mcse': error, 'absolute_error_over_mcse': z, 'passed': math.isfinite(z) and z <= 5.0})
        result['known_physical_uniform_moments'] = tests
        result['transform_control_qualified'] = limits_pass and all(x['passed'] for x in tests)
    return result
