"""Experiment-specific orchestration of external emcee/SciPy kernels and ArviZ diagnostics.

No proposal, acceptance rule, physics or likelihood kernel is implemented here.
Four chain configurations and a frozen proposal are admitted before production.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import time

NAMES = ('omega_b', 'omega_cdm', 'H0', 'logA', 'n_s', 'tau_reio', 'A_planck')
DERIVED = {'theta_s_100': '100*theta_s', 'Omega_m': 'Omega_m',
           'Omega_Lambda': 'Omega_Lambda', 'YHe': 'YHe', 'Neff': 'Neff',
           'z_reio': 'z_reio', 'z_d': 'z_d', 'r_drag_Mpc': 'r_drag_Mpc',
           'omega_ncdm': 'omega_ncdm'}


def atomic_bytes(path, raw):
    temporary = path.with_suffix(path.suffix + '.pending')
    with temporary.open('wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    directory = os.open(path.parent, os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}



def kernel_inventory():
    """Pin actually loaded external statistical code and native libraries."""
    import sys
    paths = {Path(module.__file__).resolve() for module in tuple(sys.modules.values())
             if getattr(module, '__file__', None) and '/site-packages/' in str(module.__file__)}
    for line in Path('/proc/self/maps').read_text().splitlines():
        path = line.split()[-1]
        if path.startswith('/') and '.so' in path and Path(path).is_file():
            paths.add(Path(path).resolve())
    pins = []
    for path in sorted(paths):
        before = path.stat()
        if before.st_size > 536870912:
            raise ValueError('external statistical dependency file bound')
        raw = path.read_bytes()
        after = path.stat()
        if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            raise ValueError('external statistical source changed during admission')
        pins.append({'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
    return pins


def verify_kernel_inventory(pins):
    for pin in pins:
        path = Path(pin['path'])
        if path.stat().st_size != pin['bytes'] or hashlib.sha256(path.read_bytes()).hexdigest() != pin['sha256']:
            raise ValueError('admitted external statistical source changed')


def diagnose(chain_rows, contract, configuration):
    import numpy as np
    import arviz as az
    all_quantities = [*NAMES, *DERIVED, 'logtarget']
    invariances = configuration.get('invariance_controls', {})
    if set(invariances) - {'Neff','omega_ncdm'}:
        raise ValueError('only source-fixed Neff and physical massive density may be exempt')
    quantities = [name for name in all_quantities if name not in invariances]
    if len(chain_rows) != 4:
        raise ValueError('four actual independent chains required')
    traces = []
    invariant_observations = {name:[] for name in invariances}
    for rows in chain_rows:
        weights = np.asarray([row['weight'] for row in rows])
        if np.any(weights <= 0) or np.any(weights != np.floor(weights)):
            raise ValueError('exact positive integer holding counts required')
        for name in invariances:
            invariant_observations[name].extend(float(row[name]) for row in rows)
        values = np.array([[row[q] for q in quantities] for row in rows])
        trace = np.repeat(values, weights.astype(int), axis=0)
        traces.append(trace[configuration['warmup_raw_steps']:])
    original_lengths = list(map(len,traces))
    if len(set(original_lengths)) != 1:
        raise ValueError('unequal fixed-length completed production chains: ' + str(original_lengths))
    length = original_lengths[0]
    draws = np.stack([trace[:length] for trace in traces])
    data = az.from_dict(posterior={name: draws[:,:,i] for i,name in enumerate(quantities)})
    rhat = az.rhat(data,method='rank').to_array().values
    bulk = az.ess(data,method='bulk').to_array().values
    tail = az.ess(data,method='tail').to_array().values
    mcse = az.mcse(data,method='mean').to_array().values
    sd = draws.std(axis=(0,1),ddof=1)
    diagnostics = {name:{'rank_split_rhat':float(rhat[i]), 'combined_bulk_ess':float(bulk[i]),
        'combined_tail_ess':float(tail[i]), 'mean_mcse':float(mcse[i]),
        'posterior_sd':float(sd[i]), 'mcse_over_sd':float(mcse[i]/sd[i])}
        for i,name in enumerate(quantities)}
    boundaries = {}
    for i,name in enumerate(NAMES):
        lo,hi = contract['bounds'][name]; width=hi-lo
        intervals = np.quantile(draws[:,:,i],[.025,.975])
        shells = {}
        for label,mask in [('lower',draws[:,:,i] <= lo+.05*width),
                           ('upper',draws[:,:,i] >= hi-.05*width)]:
            law = az.from_dict(posterior={'occupancy':mask.astype(float)})
            shells[label] = {'occupancy':float(mask.mean()),
                            'per_chain_occupancy':mask.mean(axis=1).tolist(),
                            'autocorrelation_mcse':float(az.mcse(law,method='mean').occupancy.values) if 0<mask.mean()<1 else None,
                            'rare_event_note':'zero observed hits is not zero posterior mass; rare-event autocorrelation uncertainty cannot be measured from a constant indicator' if mask.mean() in (0,1) else None}
        boundaries[name] = {**shells,'central_95_interval':intervals.tolist(),
                            'interval_distance_from_lower':float(intervals[0]-lo),
                            'interval_distance_from_upper':float(hi-intervals[1])}
    invariant_results = {}
    for name, values in invariant_observations.items():
        expected = invariances[name]['expected']
        tolerance = invariances[name]['absolute_tolerance']
        excursion = max(abs(value-expected) for value in values)
        invariant_results[name] = {'expected':expected,'absolute_tolerance':tolerance,
                                  'minimum':min(values),'maximum':max(values),
                                  'maximum_absolute_excursion':excursion,'passed':excursion<=tolerance}
    finite = np.all(np.isfinite([*rhat,*bulk,*tail,*mcse,*sd]))
    passed = bool(finite and np.all(rhat<1.01) and np.all(bulk>=400)
                  and np.all(tail>=400) and np.all(mcse/sd<=.05)
                  and all(value['passed'] for value in invariant_results.values()))
    return {'schema':'primary-four-chain-diagnostics/v1','diagnostics':diagnostics,
            'boundary_shells':boundaries,'source_fixed_invariance_controls':invariant_results,'aligned_raw_draws_per_chain':length,'original_postwarmup_lengths':original_lengths,
            'convergence_qualified':passed,'target_is_conditional_v2':True,
            'boundary_rule':'5% shells; >1% mass or near-bound central interval requires restriction-sensitive interpretation and separately qualified expansion before robustness claim; zero hits does not establish zero mass'}


def optimize(evaluator, configuration, attempt):
    """External SciPy optimization in frozen proposal-whitened coordinates."""
    import numpy as np
    from scipy.optimize import minimize
    start = np.asarray(configuration['start'],dtype=float)
    covariance = np.asarray(configuration['proposal_covariance'],dtype=float)
    root = np.linalg.cholesky(covariance)
    best = None
    def objective(unit_coordinates):
        nonlocal best
        physical = start + root @ unit_coordinates
        row = evaluator.score(physical.tolist())
        if row['status'] == 'physical_prior_excluded':
            return math.inf
        if best is None or row['logtarget'] > best['logtarget']:
            best = row
            atomic_bytes(attempt / 'best-evaluated-point.json',
                         (json.dumps(best,sort_keys=True,allow_nan=False)+'\n').encode())
        return -row['logtarget']
    result = minimize(objective,np.zeros(7),method='BFGS',options={
        'gtol': configuration['gradient_tolerance'],
        'eps': configuration['finite_difference_whitened_step'],
        'maxiter': configuration['maximum_iterations'], 'disp':False})
    receipt = {'schema':'external-scipy-primary-optimizer/v1','optimizer': 'scipy.optimize.minimize/BFGS',
        'success':bool(result.success),'message':str(result.message),'evaluations':int(result.nfev),
        'iterations':int(result.nit),'best_evaluated_point':best,
        'final_physical_coordinates':(start+root@result.x).tolist(),
        'inverse_hessian_whitened':result.hess_inv.tolist(),
        'boundary_contact':{name: min(best['point'][name]-evaluator.contract['bounds'][name][0],
            evaluator.contract['bounds'][name][1]-best['point'][name]) /
            (evaluator.contract['bounds'][name][1]-evaluator.contract['bounds'][name][0])
            for name in NAMES},'posterior_qualified':False}
    atomic_bytes(attempt/'optimizer.json',(json.dumps(receipt,indent=2,allow_nan=False)+'\n').encode())
    return receipt


def run_independence_chain(evaluator, configuration, attempt):
    """Four separately invoked singleton MH chains; no ensemble-dependent moves.

    SciPy owns the untruncated Student-t proposal and densities. Installed emcee
    MHMove owns the Hastings acceptance decision. The fixed symmetric A-only
    move is mixed with a fixed weight, and reuses the retained physical state.
    """
    import numpy as np
    import emcee
    from scipy.stats import multivariate_t
    import sys
    if configuration['engine'] != 'emcee-singleton-mh-t6':
        raise ValueError('explicit mature singleton MH engine identity required')
    names = list(NAMES)
    center = np.asarray(configuration['proposal_location'],dtype=float)
    shape = np.asarray(configuration['proposal_shape'],dtype=float)
    if center.shape != (7,) or shape.shape != (7,7) or not np.all(np.isfinite([*center,*shape.ravel()])):
        raise ValueError('finite frozen seven-coordinate location/shape required')
    if not np.allclose(shape,shape.T,atol=1e-14,rtol=0):
        raise ValueError('symmetric Student-t shape required')
    np.linalg.cholesky(shape)
    law = multivariate_t(loc=center,shape=shape,df=6)
    weight = configuration['independence_weight']
    if not 0 < weight <= 1 or not configuration['calibration_step'] > 0:
        raise ValueError('frozen valid mixture weight and calibration step required')
    seed = configuration['seed']
    if type(seed) is not int or not 0 <= seed < 2**32:
        raise ValueError('explicit independently seeded chain required')
    target_hash = hashlib.sha256(json.dumps({key:value for key,value in evaluator.contract.items()
        if not key.startswith('_')},sort_keys=True,separators=(',',':')).encode()).hexdigest()
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    frozen_keys = ('engine','seed','start','proposal_location','proposal_shape',
                   'independence_weight','calibration_step','runtime_identity')
    raw_count, restored = 0, None
    if configuration.get('resume_state'):
        pin = configuration['resume_state']; source = Path(pin['path'])
        if source.is_symlink() or source.stat().st_size > 1048576:
            raise ValueError('bounded previously owned checkpoint required')
        raw = source.read_bytes()
        if len(raw) != pin['bytes'] or hashlib.sha256(raw).hexdigest() != pin['sha256']:
            raise ValueError('checkpoint identity differs')
        restored = json.loads(raw)
        if (restored['schema'] != 'emcee-singleton-mh-exact-state/v1'
                or restored['target_contract_sha256'] != target_hash
                or restored['executing_source_sha256'] != code_hash
                or any(restored['configuration'].get(k) != configuration.get(k) for k in frozen_keys)
                or configuration['raw_steps'] < restored['completed_transitions']):
            raise ValueError('checkpoint source/target/frozenkernel differs')
        verify_kernel_inventory(restored['statistical_kernel_pins'])
        versions={'emcee':emcee.__version__,'numpy':np.__version__,'scipy':__import__('scipy').__version__}
        if restored['versions'] != versions:
            raise ValueError('active mature statistical kernel versions differ')
        raw_count = restored['completed_transitions']
    proposals = (attempt/'proposals.jsonl').open('x')
    states = (attempt/'states.jsonl').open('x')
    def proposal_event(kind,vector,log_ratio):
        row={'transition':raw_count+1,'move':kind,'proposal':vector[0].tolist(),
             'log_proposal_reverse_over_forward':float(log_ratio[0])}
        proposals.write(json.dumps(row,allow_nan=False)+'\n');proposals.flush();os.fsync(proposals.fileno())
    def independent(coords,rng):
        proposed = np.asarray(law.rvs(size=len(coords),random_state=rng)).reshape(coords.shape)
        ratio = np.atleast_1d(law.logpdf(coords)-law.logpdf(proposed))
        proposal_event('independent_t6',proposed,ratio)
        return proposed,ratio
    def calibration(coords,rng):
        proposed=coords.copy();proposed[:,-1]+=rng.normal(scale=configuration['calibration_step'],size=len(coords))
        ratio=np.zeros(len(coords));proposal_event('symmetric_A',proposed,ratio)
        return proposed,ratio
    def target(values):
        row=evaluator.score(values)
        if row['status']=='physical_prior_excluded':return -np.inf,{'physical_prior_excluded':True}
        blob={name:row['derived'][original] for name,original in DERIVED.items()}
        blob['logtarget']=row['logtarget']
        return row['logtarget'],blob
    moves=[(emcee.moves.MHMove(independent,ndim=7),weight)]
    if weight < 1:moves.append((emcee.moves.MHMove(calibration,ndim=7),1-weight))
    sampler=emcee.EnsembleSampler(1,7,target,moves=moves,blobs_dtype=object)
    sampler.random_state=np.random.RandomState(seed).get_state()
    state=np.asarray(configuration['start'],dtype=float).reshape(1,7)
    if restored is not None:
        saved=restored['state'];rng=saved['random_state']
        if (rng[0]!='MT19937' or len(rng[1])!=624 or any(type(x) is not int or not 0<=x<2**32 for x in rng[1])
                or not 0<=rng[2]<=624 or rng[3] not in [0,1] or not math.isfinite(rng[4])):
            raise ValueError('exact bounded mature MT19937 state required')
        rng=(rng[0],np.array(rng[1],dtype=np.uint32),int(rng[2]),int(rng[3]),float(rng[4]))
        state=emcee.State(np.array(saved['coords'],dtype=float),log_prob=np.array(saved['log_prob'],dtype=float),
                          blobs=np.array(saved['blobs'],dtype=object),random_state=rng)
    if restored is None:
        logp,blobs=sampler.compute_log_prob(state)
        if not np.all(np.isfinite(logp)):raise ValueError('finite explicit separated starting point required')
        state=emcee.State(state,log_prob=logp,blobs=blobs,random_state=sampler.random_state)
    kernel_pins=kernel_inventory()
    if restored is not None and kernel_pins != restored['statistical_kernel_pins']:
        raise ValueError('currently loaded statistical executable closure differs from checkpoint')
    atomic_bytes(attempt/'statistical-kernel-inventory.json',(json.dumps(kernel_pins,sort_keys=True)+'\n').encode())
    def checkpoint(phase):
        value={'schema':'emcee-singleton-mh-exact-state/v1','phase':phase,
               'configuration':configuration,'target_contract_sha256':target_hash,
               'executing_source_sha256':code_hash,'completed_transitions':raw_count,
               'state':{'coords':state.coords.tolist(),'log_prob':state.log_prob.tolist(),
                        'blobs':state.blobs.tolist(),'random_state':[state.random_state[0],
                            state.random_state[1].tolist(),state.random_state[2],
                            state.random_state[3],state.random_state[4]]},
               'statistical_kernel_pins':kernel_pins,
               'versions':{'emcee':emcee.__version__,'numpy':np.__version__,'scipy':__import__('scipy').__version__},
               'evaluator_count':evaluator.count}
        pin=atomic_bytes(attempt/'statistical-state.json',(json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode())
        atomic_bytes(attempt/'statistical-state-receipt.json',(json.dumps({**pin,'completed_transitions':raw_count,
            'phase':phase,'seed':seed,'current_point':state.coords[0].tolist()},sort_keys=True)+'\n').encode())
    checkpoint('initialized')
    try:
        remaining=configuration['raw_steps']-raw_count
        # MHMove is valid for a single chain; bypass only the ensemble-rank
        # initial-state check intended for ensemble-dependent moves.
        for state in sampler.sample(state,iterations=remaining,store=False,skip_initial_state_check=True):
            if configuration.get('global_stop_path') and Path(configuration['global_stop_path']).exists():
                raise RuntimeError('another target chain failed; global stop')
            raw_count+=1
            blob=state.blobs[0]
            if type(blob) is not dict:raise ValueError('exact mature MH blob receipt required')
            row={name:float(x) for name,x in zip(names,state.coords[0])}
            row.update({name:float(x) for name,x in blob.items()})
            row.update(transition=raw_count,weight=1,logtarget=float(state.log_prob[0]))
            states.write(json.dumps(row,allow_nan=False)+'\n');states.flush();os.fsync(states.fileno())
            checkpoint('production')
        checkpoint('completed')
        return {'status':'completed','raw_transitions':raw_count,'evaluator_calls':evaluator.count,
                'seed':seed,'single_walker_independent_chain':True,'production_adaptation':False,
                'proposal_df':6,'proposal_shape_is_not_covariance':True,
                'proposal_covariance':(1.5*shape).tolist(),'inference_qualified':False}
    except BaseException:
        if configuration.get('global_stop_path'):
            atomic_bytes(Path(configuration['global_stop_path']),b'target chain refused; inspect owned prefix\n')
        raise
    finally:
        proposals.close();states.close()
        original_error=sys.exception()
        try:verify_kernel_inventory(kernel_pins)
        except BaseException as verification:
            if original_error is not None:
                original_error.add_note('Statistical after-admission also refused: '+str(verification))
            else:raise
