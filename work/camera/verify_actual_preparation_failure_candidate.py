import json,hashlib
from pathlib import Path
raw=Path('work/camera/prototype-runs/owned-native-1791539746701185000.json');r=json.loads(raw.read_text());assert r['result']=='FAILED' and 'Preparation failed' in str(r['error'])
s=r['shutdown_evidence'];assert not s['gpu_thread_alive'] and not s['preparation_thread_alive'] and s['native_owner_released'] and s['active_contexts_after_close']==0
f=r['frame_preparation_shutdown'];assert f['joined'] and f['pending']==0 and f['owner_alive_after_preparation_join'] and f['owner_released_after_renderer_close']
c=r['background_copy_shutdown'];assert not c['thread_alive'] and c['pending']==0 and c['counts']['admitted']==c['counts']['published']+c['counts']['retired']
h=r['hud_lease_cleanup'];assert h['owner_stats']==[0,0,0]
for name,digest in json.loads(Path('outputs/nfsug-native-renderer/camera-research/checkpoints/native-committed-sample-20261006/protected-hashes.json').read_text()).items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest().upper()==digest.upper()
result=dict(result='PASS_EXPECTED_PREPARATION_FAILURE_OWNER_HASH_AUDIT',shutdown=s,preparation=f,hud=h,scope='ActualexpectedFAILED report retained, cleanup andprotectedhash verified; not a successful gameplay/timingrun.')
Path('work/camera/prototype-runs/actual-preparation-failure-audit-20261009.json').write_text(json.dumps(result,indent=2));print(result['result'])
