import json,hashlib
from pathlib import Path
p=Path('work/camera/prototype-runs');r=json.loads((p/'owned-native-1791425748214806700.json').read_text());s=r['shutdown_evidence'];pool=json.loads((p/'pool-cleanup-1791425747463812600.json').read_text())
assert not s['gpu_thread_alive'] and not s['preparation_thread_alive'] and s['native_owner_released']
for k in ('gpu_queries_after_close','gpu_fences_after_close','active_contexts_after_close','retained_scene_count','pending_scene_count','prepared_result_count'):assert s[k]==0
assert pool['targets']==[0]*5 and pool['fences'][0]==pool['fences'][1] and pool['fences'][3]==0
h=json.loads(Path('outputs/nfsug-native-renderer/camera-research/checkpoints/native-committed-sample-20261006/protected-hashes.json').read_text());assert all(hashlib.sha256(Path(k).read_bytes()).hexdigest().upper()==v for k,v in h.items())
Path('work/camera/async-crop-minute-cleanup.json').write_text(json.dumps(dict(result='PASS',shutdown=s,pool=pool,protected_hashes_exact=True,pause_exercised=False),indent=2));print('PASS cleanup/protected assets; pause was not exercised')
