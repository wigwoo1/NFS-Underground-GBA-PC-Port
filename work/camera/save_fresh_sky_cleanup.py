import json,hashlib,shutil
from pathlib import Path
p=Path('work/camera/prototype-runs'); cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/fresh-later-sky-20261008')
rp=p/'owned-native-1791432584635884900.json';pp=p/'pool-cleanup-1791432584531736500.json'
r=json.loads(rp.read_text());s=r['shutdown_evidence'];pool=json.loads(pp.read_text())
assert not s['gpu_thread_alive'] and not s['preparation_thread_alive'] and s['native_owner_released']
for k in ('gpu_queries_after_close','gpu_fences_after_close','active_contexts_after_close','retained_scene_count','pending_scene_count','prepared_result_count'):assert s[k]==0
assert pool['targets']==[0]*5 and pool['fences'][0]==pool['fences'][1] and pool['fences'][3]==0
hp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/native-committed-sample-20261006/protected-hashes.json');h=json.loads(hp.read_text());assert all(hashlib.sha256(Path(k).read_bytes()).hexdigest().upper()==v for k,v in h.items())
(cp/'cleanup.json').write_text(json.dumps(dict(result='PASS',shutdown=s,pool=pool,protected_assets_exact=True),indent=2))
for x in (rp,pp,p/'selected-sky-pixels-1791432585089877300.json',Path('work/camera/run_fresh_later_sky_diagnostic.py'),Path('work/camera/live-sky-selected-fresh-400.png')):shutil.copy2(x,cp/x.name)
print('PASS cleanup and protected assets')
