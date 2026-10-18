import json,hashlib,shutil
from pathlib import Path
p=Path('work/camera/prototype-runs');cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/playable-launcher-minute-20261007');r=json.loads((p/'owned-native-1791421911515525700.json').read_text());s=r['shutdown_evidence'];pool=json.loads((p/'pool-cleanup-1791421910953312100.json').read_text());assert r['result']=='SMOKE_COMPLETE' and not s['gpu_thread_alive'] and not s['preparation_thread_alive'] and s['native_owner_released']
for k in ('gpu_queries_after_close','gpu_fences_after_close','active_contexts_after_close','retained_scene_count','pending_scene_count','prepared_result_count'):assert s[k]==0
assert pool['targets']==[0]*5 and pool['fences'][0]==pool['fences'][1] and pool['fences'][3]==0
hp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/native-committed-sample-20261006/protected-hashes.json');h=json.loads(hp.read_text());assert {k:hashlib.sha256(Path(k).read_bytes()).hexdigest().upper() for k in h}==h
for path in (p/'owned-native-1791421911515525700.json',p/'pool-cleanup-1791421910953312100.json',hp):shutil.copy2(path,cp/path.name)
(cp/'cleanup.json').write_text(json.dumps(dict(result='PASS',shutdown=s,pool=pool,protected_hashes_exact=True,original_admission_audit='NOT_AVAILABLE: producer-cycles disabled; original_update_samples not populated'),indent=2))
c=json.loads((cp/'sky-cadence.json').read_text());print(json.dumps(dict(cadence=c['active_presentation_cadence'],gate=c['cpu_cadence_gate'],moving=c['moving_same_pair_transitions'],frozen=c['frozen_moving_transitions'])))
