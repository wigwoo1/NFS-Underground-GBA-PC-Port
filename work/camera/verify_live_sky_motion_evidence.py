"""Audit captured runtime invariants without equating CPU records to scanout."""
import json,struct,sys,math
from pathlib import Path
from analyze_active_play_cadence import analyze

def verify(r):
 assert r['timing']['original_clock_hz']==16777216 and r['timing']['cycles_per_update']==280896
 assert abs(r['timing']['simulated_seconds']-r['original_updates']*280896/16777216)<1e-9
 continuous=r.get('sky_continuous_enabled',False)
 sky_sources={};phase_checks=0
 if continuous:
  for source in r['sky_capture_records']:
   key=(source['epoch'],source['publication'])
   assert key not in sky_sources,'Duplicate sky source identity'
   assert 0<=source['angle']<2**32
   sky_sources[key]=source
 rows=[x for x in r['presentation_samples'] if x.get('interpolated') and x.get('hidden_window_presented')];assert rows
 for i,x in enumerate(rows):
  c=x['native_committed_sample'];assert c
  assert c[:5]==[x['epoch'],x['generation'],x['source_older'],x['refresh'],x['display_index']]
  assert struct.unpack('<d',struct.pack('<Q',c[5]))[0]==x['alpha']
  if continuous:
   assert x.get('sky_phase_mode')=='continuous_angle','Wrong sky phase mode'
   older=sky_sources[x['epoch'],x['source_older']];newer=sky_sources[x['epoch'],x['refresh']]
   assert older['asset_origin']==newer['asset_origin'],'Sky asset changed within pair'
   delta=((newer['angle']-older['angle']+8192)&16383)-8192
   assert abs(delta*240/4096)<120,'Ambiguous sky phase interval'
   assert math.isfinite(x['alpha']) and 0<=x['alpha']<=1
   angle=(newer['angle']&16383) if x['alpha']==1 else (older['angle']&16383)+delta*x['alpha']
   phase=(angle*240/4096)%240
   assert x['sky_fraction']==phase-math.floor(phase),'Sky phase differs from captured camera angle'
   phase_checks+=1
  assert x['sky_interpolated'] and x['full_scene_sampled'] and x['complete_scene_pair_retained']
  if x.get('native_deadline_path'):
   stages=x['stages'];assert len(stages)==7 and stages==sorted(stages)
   t=x['callback_timing'];assert t['present_begin_ns']==stages[3] and t['present_end_ns']==stages[4]
   assert x['presentation']['status']==0 and x['native_result']==1
   assert stages[4]<=c[6]<=x['transaction_end_ns'] and c[6]>=x['presentation_deadline_ns']
  else:
   assert x['present_end_ns']>=x['present_begin_ns']
   assert x['present_begin_ns']<=c[6]<=x['commit_return_ns'] and c[6]>=x['presentation_deadline_ns']
  if i:
   prev=rows[i-1];assert x['display_index']>prev['display_index']
   if x['epoch']==prev['epoch']:assert c[7]==prev['native_committed_sample'][7]+1
 shutdown=r['shutdown_evidence'];assert shutdown['active_contexts_after_close']==0 and not shutdown['gpu_thread_alive'] and not shutdown['preparation_thread_alive'] and shutdown['native_owner_released']
 a=analyze(r)
 return dict(continuous_sky_phase_checks=phase_checks,result='PASS_CAPTURED_INVARIANTS',committed_fullscene_sky_samples=len(rows),original_clock_constants_verified=True,clean_shutdown=True,cadence=a,cpu_cadence_gate=a['contiguous'] and abs(a['active_clock_ratio']-1)<.005 and a['active_gaps_over_two_refreshes']==0,physical_scanout_verified=False,independent_visual_fidelity_verified=False,physical_controller_verified=r['physical_controller_verified'],scope='Exact captured source/sample/native publication/original cycle constants; CPU cadence gate is necessary diagnostic evidence, never sufficient full gameplay or scanout certification.')
if __name__=='__main__':
 p=Path(sys.argv[1]);out=verify(json.loads(p.read_text()));p.with_suffix('.motion-audit.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
