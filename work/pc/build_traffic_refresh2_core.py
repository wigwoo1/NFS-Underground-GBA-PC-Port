"""One refresh per producer at the two independently observed multiply stages."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess
source=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');baseline=base/'NFSUG-pc-traffic-refresh-core';out=base/'NFSUG-pc-traffic-refresh2-core';out.mkdir(exist_ok=True);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((baseline/'traffic-refresh-build-report.json').read_text());progress=json.loads((baseline/'traffic-refresh-progress-report.json').read_text());proof=base/'NFSUG-pc-traffic-refresh-primary-failure-probe/primary-rejection-analysis.json';e=json.loads(proof.read_text())
assert progress['new_late_source_misses']==9 and r['core_sha256']==progress['core_sha256']==sha(baseline/'capture-host.dll')
assert e['primary_pc']=='0x8022d38' and e['primary_phase']==0 and e['refresh_delta']==1 and e['primary_token_mask']==8 and e['primary_matches_failed_model'] and e['same_camera_bytes'] and e['same_object_index'] and e['same_epoch'] and e['same_scene']
for n,h in r['maintained_source_sha256'].items():assert sha(source/n)==h,n
for n,h in r['staged_input_sha256'].items():assert sha(baseline/'source'/n)==h,n
staged=out/'source';shutil.copytree(baseline/'source',staged,dirs_exist_ok=True);shutil.copy2(source/'traffic_rotation_refresh2_capture.inc',staged/'traffic_rotation_refresh2_capture.inc');p=staged/'camera/live_scene.h';s=p.read_text();a='#include "../traffic_rotation_refresh_capture.inc"';assert s.count(a)==1;p.write_text(s.replace(a,'#include "../traffic_rotation_refresh2_capture.inc"'))
cmd=[a.replace(str(baseline/'source'),str(staged)).replace(str(baseline/'capture-host.dll'),str(out/'capture-host.dll')) for a in r['command']];env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
with (out/'build.log').open('w') as log:subprocess.run(cmd,env=env,check=True,stdout=log,stderr=subprocess.STDOUT)
b=dict(result='BUILT_SINGLE_CROSSING_TWO_STAGE_TRAFFIC_CORE',command=cmd,core_sha256=sha(out/'capture-host.dll'),baseline_core_sha256=r['core_sha256'],baseline_build_sha256=sha(baseline/'traffic-refresh-build-report.json'),baseline_progress_sha256=sha(baseline/'traffic-refresh-progress-report.json'),failure_evidence_sha256=sha(proof),maintained_source_sha256=dict(r['maintained_source_sha256'],**{'traffic_rotation_refresh2_capture.inc':sha(source/'traffic_rotation_refresh2_capture.inc')}),staged_input_sha256={str(p.relative_to(staged)):sha(p) for p in staged.rglob('*') if p.is_file()},script_sha256=sha(Path(__file__)),game_logic_changed=False,full_scene_60fps=False,live_integration_verified=False)
(out/'traffic-refresh2-build-report.json').write_text(json.dumps(b,indent=2));print(b['result'],b['core_sha256'])
