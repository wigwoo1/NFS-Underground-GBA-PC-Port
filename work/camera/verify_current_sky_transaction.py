"""Current native transaction sky evidence; retained records, never scanout certification."""
import json,math,struct,sys,copy
from pathlib import Path

def verify(r):
 t=r['timing'];assert t['original_clock_hz']==16777216 and t['cycles_per_update']==280896
 sources={}
 for s in r['sky_capture_records']:
  key=(s['epoch'],s['publication']);assert key not in sources
  assert 0<=s['angle']<2**32;sources[key]=s
 rows=r['presentation_samples'];assert rows
 phases=[]
 for x in rows:
  assert all(x[k] for k in ('interpolated','hidden_window_presented','full_scene_sampled','sky_interpolated','complete_scene_pair_retained'))
  assert x['sky_phase_mode']=='continuous_angle' and 0<=x['alpha']<=1 and math.isfinite(x['alpha'])
  a=sources[x['epoch'],x['source_older']];b=sources[x['epoch'],x['refresh']]
  assert a['asset_origin']==b['asset_origin'];d=((b['angle']-a['angle']+8192)&16383)-8192;assert abs(d*240/4096)<120
  angle=(b['angle']&16383) if x['alpha']==1 else (a['angle']&16383)+d*x['alpha'];phase=angle*240/4096%240
  assert x['sky_fraction']==phase-math.floor(phase);phases.append(phase)
  n=x['native_transaction'];c=n['commit'];assert c==x['commit']==x['native_committed_sample']
  assert c[:5]==[x['epoch'],x['generation'],x['source_older'],x['refresh'],x['display_index']]
  assert struct.unpack('<d',struct.pack('<Q',c[5]))[0]==x['alpha']
  assert n['native_result']==x['native_result']==1 and n['presentation']['status']==0
  stamps=n['stages'];assert len(stamps)==7 and stamps==sorted(stamps)
  assert n['transaction_begin_ns']<=stamps[0]<=stamps[4]<=c[6]<=n['transaction_end_ns'] and c[6]>=x['presentation_deadline_ns']
  assert n['wait'][1]==x['presentation_deadline_ns']
 q=r['shutdown_evidence'];s=q['preparation_service_shutdown']
 assert q['native_owner_released'] and q['active_contexts_after_close']==0 and not q['gpu_thread_alive']
 assert not s['child_alive'] and not s['preparation_thread_alive'] and s['child_exitcode']==0 and not s['errors']
 moving=held=0
 for i in range(1,len(rows)):
  a,b=rows[i-1:i+1];assert b['display_index']>a['display_index']
  if (a['epoch'],a['generation'])!=(b['epoch'],b['generation']):continue
  assert b['commit'][7]>a['commit'][7]
  if abs((phases[i]-phases[i-1]+120)%240-120)>1e-9:moving+=1
  else:held+=1
 return dict(result='PASS_CURRENT_RETAINED_SKY_TRANSACTION_INVARIANTS',samples=len(rows),moving_transitions=moving,held_transitions=held,clean_shutdown=True,physical_scanout_verified=False,scope='Retained phase/source/native transaction identity and cleanup. Not full-run sky pixels, sustained60 or physical scanout.')

if __name__=='__main__':
 root=Path(r'G:\EXTRA DATA DRIVE\Desktop\Games\Codex\NFSUG-Native-PC-Port')
 p=Path(sys.argv[1]) if len(sys.argv)>1 else max((root/'work/camera/prototype-runs').glob('owned-native-*.json'),key=lambda p:p.stat().st_mtime)
 r=json.loads(p.read_text());out=verify(r);rejected=[]
 for kind in ('phase','alpha','commit_identity','early_commit','asset','shutdown','missing_stage'):
  b=copy.deepcopy(r);x=b['presentation_samples'][0]
  if kind=='phase':x['sky_fraction']=(x['sky_fraction']+.2)%1
  elif kind=='alpha':x['alpha']=float('nan')
  elif kind=='commit_identity':x['native_transaction']['commit'][0]+=1
  elif kind=='early_commit':x['native_transaction']['commit'][6]=x['presentation_deadline_ns']-1
  elif kind=='asset':next(s for s in b['sky_capture_records'] if (s['epoch'],s['publication'])==(x['epoch'],x['refresh']))['asset_origin']+=1
  elif kind=='shutdown':b['shutdown_evidence']['preparation_service_shutdown']['child_alive']=True
  else:x['native_transaction']['stages'].pop()
  try:verify(b)
  except (AssertionError,KeyError):rejected.append(kind)
  else:raise AssertionError('Mutation accepted: '+kind)
 out.update(report=str(p),rejected_mutations=rejected);Path('current_sky_transaction_audit.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
