"""Audit native live integration without treating occlusion as presentation success."""
import json,sys,hashlib,collections
from pathlib import Path
checks=[]
for name in sys.argv[1:]:
 r=json.loads(Path(name).read_text());assert r['result']=='SMOKE_COMPLETE' and r['error'] is None
 t=r['timing'];assert t['original_clock_hz']==16777216 and t['cycles_per_update']==280896
 assert abs(t['simulated_seconds']-r['original_updates']*280896/16777216)<1e-9
 rows=r['presentation_samples'];assert rows and all(x['native_d3d_candidate'] and x['context_count']==0 and x['full_scene_sampled'] and x['sky_interpolated'] for x in rows)
 indices=[x['display_index'] for x in rows];assert indices==sorted(indices)
 previous_by_index={}
 for row in rows:
  index=row['display_index']
  if index in previous_by_index:
   prior=previous_by_index[index]
   assert prior['native_result']==0 and row['generation']>prior['generation'] and row['epoch']==prior['epoch'],'Repeated non-cancelled slot'
  previous_by_index[index]=row
 committed=[x['display_index'] for x in rows if x['native_result']==1];assert len(committed)==len(set(committed))
 for x in rows:
  if x['native_result']==1:assert x['presentation']['status']==0 and x['native_committed_sample']
  else:assert x['native_committed_sample'] is None
  if x.get('prepared'):assert x['prepared']['publication'][:3]==[x['epoch'],x['generation'],x['display_index']]
 s=r['shutdown_evidence'];assert not s['gpu_thread_alive'] and not s['preparation_thread_alive'] and s['native_owner_released'] and s['active_contexts_after_close']==0 and s['pending_scene_count']==0
 checks.append(dict(report=name,updates=r['original_updates'],samples=len(rows),pause_events=len(r['pause_events']),native_results=dict(collections.Counter(x['native_result'] for x in rows)),successful_native_presentations=sum(x['native_result']==1 for x in rows),physical_scanout_verified=False))
protected=json.loads(Path('outputs/nfsug-native-renderer/camera-research/checkpoints/native-committed-sample-20261006/protected-hashes.json').read_text())
for name,digest in protected.items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest().upper()==digest.upper(),name
out=dict(result='PASS_LIVE_NATIVE_INTEGRATION',checks=checks,protected_files_verified=len(protected),scope='Actual original-clock live capture/native scene submission and scripted pause lifecycle; successful native Present calls counted separately; physical scanout, fullscene60fps, independent route fidelity and physical Xbox remain unverified')
Path('work/camera/prototype-runs/native-d3d-live-integration-audit.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
