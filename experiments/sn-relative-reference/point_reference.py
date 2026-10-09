"""Actual relative-SN direct CLASS distances and retained native Gaussian kernel."""
import argparse, hashlib, importlib.util, json, math, os, pathlib, struct, subprocess, sys, time
import numpy as np
import scipy.linalg as la

def pin(p):
 p=pathlib.Path(p).resolve();return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def emit(p,j):p.write_text(json.dumps(j,indent=2,allow_nan=False)+'\n')
def payload(p,a):p.write_bytes(np.asarray(a,dtype='>f8').tobytes());return {**pin(p),'shape':list(a.shape),'dtype':'IEEE754 binary64 big-endian','order':'original occurrence row order'}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--policy',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();out=pathlib.Path(a.output);p=json.loads(pathlib.Path(a.policy).read_text());start=time.monotonic();record={'schema':'sn-relative-actual-model-point-reference/v1','status':'running','policy_pin':pin(a.policy),'source_pin':pin(__file__),'posterior_qualified':False,'evaluations':[]};native=None;owner=None;native_log=None
 try:
  for expected in p['inputs']:
   actual=pin(expected['path']);assert actual['bytes']==expected['bytes'] and actual['sha256']==expected['sha256']
  sel=json.loads(pathlib.Path(p['selection_path']).read_text());indices=np.asarray(sel['selected_original_indices'],dtype=np.int64);rows=sel['row_fields_original_lexical'];assert len(indices)==1590
  table=pathlib.Path(p['table_path']).read_bytes();lines=table.decode('ascii').splitlines();header=lines[0].split();source_rows=[dict(zip(header,x.split())) for x in lines[1:]];assert len(source_rows)==1701 and list(indices)==[i for i,x in enumerate(source_rows) if float(x['zHD'])>.01]
  for i in indices:
   for name,value in rows[int(i)]['source_lexical_fields'].items():assert source_rows[int(i)][name]==value
  observed=np.array([float(source_rows[int(i)]['m_b_corr']) for i in indices]);zhd=np.array([float(source_rows[int(i)]['zHD']) for i in indices]);zhel=np.array([float(source_rows[int(i)]['zHEL']) for i in indices]);flags=np.array([bool(int(source_rows[int(i)]['IS_CALIBRATOR'])) for i in indices]);assert flags.sum()==10
  # This controls the observer-frame formula using independent literal product122.1.
  assert abs(float(5*np.log10((1+.1)*(1+.11)*100)+25)-(5*math.log10(122.1)+25))<1e-12
  covariance=np.fromfile(p['covariance_path'],dtype='>f8').astype(np.float64).reshape(1590,1590);assert np.all(np.isfinite(covariance)) and np.array_equal(covariance,covariance.T)
  L=la.cholesky(covariance,lower=True);logdet=float(2*np.sum(np.log(np.diag(L).astype(np.longdouble)),dtype=np.longdouble));ones=np.ones(1590);wones=la.cho_solve((L,True),ones);gram=float(ones@wones)
  extension=pathlib.Path(p['classy_extension_path']);sys.path.insert(0,str(extension.parent));import classy
  assert pin(classy.__file__)['sha256']==pin(extension)['sha256'];owner=classy.Class()
  spec=importlib.util.spec_from_file_location('owned_runtime_fingerprint',p['runtime_fingerprint_source']);rt=importlib.util.module_from_spec(spec);spec.loader.exec_module(rt);before=rt.runtime();emit(out/'runtime-before.json',before);assert all(x['num_threads']==1 for x in before['threadpools']) and before['versions']==p['runtime_versions']
  native_log=(out/'native-stderr.log').open('xb');native=subprocess.Popen([p['native_binary'],p['covariance_path'],p['indices_path'],p['indices_sha256']],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=native_log)
  ready=json.loads(native.stdout.readline());assert ready['status']=='ready' and ready['rows']==1590 and ready['covariance_sha256']==p['covariance_sha256'];record['native_ready']=ready
  native_maps=sorted({line.split(maxsplit=5)[5] for line in pathlib.Path(f'/proc/{native.pid}/maps').read_text().splitlines() if len(line.split(maxsplit=5))==6 and line.split(maxsplit=5)[5].startswith('/') and pathlib.Path(line.split(maxsplit=5)[5]).is_file()});record['native_loaded_files']=[pin(x) for x in native_maps]
  log=(out/'evaluations.jsonl').open('x');seq=0;comparisons={};best=None
  def evaluate(case,precision,M,mu,parameters,fit_label):
   nonlocal seq,best
   residual=(observed-mu)-M;wire=np.asarray(residual,dtype='>f8').tobytes();native.stdin.write(struct.pack('>QQ',seq,1590)+wire);native.stdin.flush();raw=native.stdout.readline();v=json.loads(raw);assert v['status']=='finite' and v['sequence']==seq and v['residual_sha256']==hashlib.sha256(wire).hexdigest()
   wr=la.solve_triangular(L,residual,lower=True);q=float(np.sum(wr.astype(np.longdouble)**2,dtype=np.longdouble));lnref=-.5*(q+logdet+1590*math.log(2*math.pi));difference=v['loglike']-lnref;assert abs(difference)<=p['maximum_native_reference_delta_lnL']
   deltaMref=float((wones@residual)/gram);assert abs(v['profile_delta_M']-deltaMref)<=p['maximum_profile_M_difference_mag']
   row={'sequence':seq,'case':case,'precision':precision,'M_mag':M,'fit_label':fit_label,'source_selection':'relative1590;allrows cosmologicalmean including10calflags','parameters':parameters,'residual':payload(out/f'residual-{seq:03d}.f64be',residual),'native':v,'independent_reference':{'quadratic':q,'logdet':logdet,'normalization':1590*math.log(2*math.pi),'loglike':lnref,'profile_delta_M':deltaMref},'native_reference_delta_lnL':difference,'proper_logprior':p['proper_logprior'],'proper_logtarget':v['loglike']+p['proper_logprior']}
   log.write(json.dumps(row,allow_nan=False)+'\n');log.flush();record['evaluations'].append({'sequence':seq,'case':case,'precision':precision,'M_mag':M,'native_loglike':v['loglike'],'native_reference_delta_lnL':difference});seq+=1
   if precision=='production' and (best is None or row['proper_logtarget']>best['proper_logtarget']):best={'case':case,'M_mag':M,'proper_logtarget':row['proper_logtarget'],'native_loglike':v['loglike'],'optimizer_scope':'finite pilot backgrounds, bounded sharedMconditional optimizer; no global cosmologicaloptimum or posterior'}
   return row
  for case in p['cosmological_points']:
   for precision,settings in p['background_policies'].items():
    pars={**p['class_physical_fixed'],**case['values'],**settings};owner.set(pars);owner.compute(['background']);omega_lambda=owner.Omega_Lambda();assert math.isfinite(omega_lambda) and omega_lambda>=0
    DA=np.asarray(owner.angular_distance(zhd),dtype=np.float64);DL=np.asarray(owner.luminosity_distance(zhd),dtype=np.float64);assert DA.shape==(1590,) and np.all(np.isfinite(DA)) and np.all(DA>0);assert np.max(np.abs(DL/(DA*(1+zhd)**2)-1))<=2e-12
    mu=5*np.log10((1+zhd)*(1+zhel)*DA)+25;distance={'case':case['id'],'precision':precision,'parameters':pars,'Omega_Lambda':omega_lambda,'omega_ncdm_today':float(owner.Omega_nu*owner.h()**2),'DA':payload(out/f"{case['id']}-{precision}-DA.f64be",DA),'mu_without_M':payload(out/f"{case['id']}-{precision}-mu.f64be",mu),'all_relative_rows_use_cosmology':True,'calibrator_flags_retained':10};emit(out/f"{case['id']}-{precision}-distance.json",distance)
    results=[]
    for M in p['M_controls']:results.append(evaluate(case['id'],precision,M,mu,pars,'predeclared_fixedMcontrol'))
    center=results[1];unboundedM=center['M_mag']+center['native']['profile_delta_M'];boundedM=min(p['priors']['M'][1],max(p['priors']['M'][0],unboundedM));opt=evaluate(case['id'],precision,boundedM,mu,pars,'bounded_flat_prior_conditionalM_optimizer');opt['unbounded_profile_M']=unboundedM;opt['M_optimizer_boundary_contact']=boundedM!=unboundedM;emit(out/f"{case['id']}-{precision}-conditionalM-fit.json",opt);comparisons[(case['id'],precision)]=[x['native']['loglike'] for x in results]+[opt['native']['loglike']]
    owner.struct_cleanup();owner.empty()
  log.close();refinements=[]
  for case in p['cosmological_points']:
   prod,ref1,ref2=[comparisons[(case['id'],x)] for x in ('production','reference1','reference2')];d1=max(abs(x-y) for x,y in zip(prod,ref1));d2=max(abs(x-y) for x,y in zip(ref1,ref2));refinements.append({'case':case['id'],'maximum_production_reference1_delta_lnL':d1,'maximum_reference1_reference2_delta_lnL':d2,'budget':p['maximum_background_refinement_delta_lnL'],'passed':max(d1,d2)<=p['maximum_background_refinement_delta_lnL']})
  record['background_refinements']=refinements;record['finite_pilot_best']=best;record['actual_data_model_evaluated']=True;record['source_frame_and_distance_duality_controls_passed']=True
  native.stdin.write(struct.pack('>QQ',2**64-1,0));native.stdin.close();closed=json.loads(native.stdout.readline());assert closed['status']=='closed' and closed['evaluations']==seq;assert native.wait(timeout=10)==0;record['native_closed']=closed
  after=rt.runtime();emit(out/'runtime-after.json',after);assert before==after;record['runtime_unchanged']=True
  for expected in p['inputs']:
   actual=pin(expected['path']);assert actual['sha256']==expected['sha256'] and actual['bytes']==expected['bytes']
  record['status']='actual_points_and_conditionalM_fits_qualified' if all(x['passed'] for x in refinements) else 'background_refinement_refused';record['posterior_qualified']=False
  assert sum(x.stat().st_size for x in out.rglob('*') if x.is_file())<=p['limits']['output_final_admission_max_bytes']
 except BaseException as e:record['status']='refused';record['error']={'type':type(e).__name__,'message':str(e)};raise
 finally:
  if native is not None and native.poll() is None:native.kill();native.wait()
  if native_log is not None:native_log.close()
  if owner is not None:
   try:owner.struct_cleanup();owner.empty()
   except Exception:pass
  record['elapsed_seconds']=time.monotonic()-start;emit(out/'terminal.json',record)
if __name__=='__main__':main()
