"""Audit launcher behavior without certifying physical scanout or controller input."""
import json,sys,runpy,shutil,hashlib
from pathlib import Path
from analyze_live_sky_cadence import analyze
from verify_pause_replay_commits import verify
rp,pp,cp=map(Path,sys.argv[1:4]);cp.mkdir(exist_ok=True);r=json.loads(rp.read_text());s=r['shutdown_evidence']
assert r['result']=='SMOKE_COMPLETE' and not s['gpu_thread_alive'] and not s['preparation_thread_alive'] and s['native_owner_released']
for k in ('gpu_queries_after_close','gpu_fences_after_close','active_contexts_after_close','retained_scene_count','pending_scene_count','prepared_result_count'):assert s[k]==0
pool=json.loads(pp.read_text());assert pool['targets']==[0]*5 and pool['fences'][0]==pool['fences'][1] and pool['fences'][3]==0
if r['quit_while_paused']:
 p=s['open_pause'];assert p['begin_ns']<=p['native_pause_ack_ns']<=p['close_begin_ns']<=s['close_completed_ns'];commits=[x['native_committed_sample'] for x in r['presentation_samples'] if x.get('native_committed_sample')];assert commits and all(x[6]<p['native_pause_ack_ns'] for x in commits);(cp/'quit-paused.json').write_text(json.dumps(dict(result='PASS',commits=len(commits)),indent=2))
else:
 assert len(r['pause_events'])==3
 for name,value in [('sky-cadence',analyze(r)),('pause-replay',verify(r))]:(cp/(name+'.json')).write_text(json.dumps(value,indent=2))
 sys.argv=['verify_native_pause_ack.py',str(rp),str(cp/'pause-ack.json')];runpy.run_path(str(Path(__file__).parent/'verify_native_pause_ack.py'),run_name='__main__')
sys.argv=['verify_original_update_deadlines.py',str(rp),str(cp/'original-timing.json')];runpy.run_path(str(Path(__file__).parent/'verify_original_update_deadlines.py'),run_name='__main__')
hp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/native-committed-sample-20261006/protected-hashes.json');h=json.loads(hp.read_text());assert {k:hashlib.sha256(Path(k).read_bytes()).hexdigest().upper() for k in h}==h
for path in (rp,pp,hp,Path(__file__),Path('PLAYABLE TIMING PROTOTYPE.cmd')):shutil.copy2(path,cp/path.name)
(cp/'cleanup.json').write_text(json.dumps(dict(result='PASS',shutdown=s,pool=pool,protected_hashes_exact=True),indent=2));print('Launcher lifecycle/protected-assets audit PASS; original admission audit does not certify realtime timing')
if not r['quit_while_paused']:
 cadence=json.loads((cp/'sky-cadence.json').read_text());print('Active CPU presentation cadence gate:',cadence['cpu_cadence_gate'])
