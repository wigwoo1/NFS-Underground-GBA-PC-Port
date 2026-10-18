"""Isolated exact-stage one-refresh producer handoff over verified traffic core."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess
source=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');baseline=base/'NFSUG-pc-traffic-rotation-draw-camera-core';out=base/'NFSUG-pc-traffic-refresh-core';out.mkdir(exist_ok=True);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((baseline/'traffic-draw-camera-build-report.json').read_text());t=json.loads((baseline/'traffic-draw-camera-core-test-report.json').read_text());proof=base/'NFSUG-pc-traffic-remaining-primary-failure-core/traffic-remaining-primary-milestone-report.json';e=json.loads(proof.read_text())
assert r['core_sha256']==t['core_sha256']==sha(baseline/'capture-host.dll') and e['result']=='VERIFIED_FIRST_REMAINING_GAP_IS_ONE_REFRESH_PRODUCER_TOKEN_REJECTION'
assert e['scene']==871 and e['producer_phase']==1 and e['initiating_producer_pc']=='0x8022d44' and e['same_camera_bytes_at_initiating_failure'] and e['same_object_index']
for n,h in r['maintained_source_sha256'].items():assert sha(source/n)==h,n
for n,h in r['staged_input_sha256'].items():assert sha(baseline/'source'/n)==h,n
staged=out/'source';shutil.copytree(baseline/'source',staged,dirs_exist_ok=True);shutil.copy2(source/'traffic_rotation_refresh_capture.inc',staged/'traffic_rotation_refresh_capture.inc')
h=staged/'camera/live_scene.h';s=h.read_text();a='#include "../traffic_rotation_draw_capture.inc"';assert s.count(a)==1;h.write_text(s.replace(a,'#include "../traffic_rotation_refresh_capture.inc"'))
cmd=[a.replace(str(baseline/'source'),str(staged)).replace(str(baseline/'capture-host.dll'),str(out/'capture-host.dll')) for a in r['command']];env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
with (out/'build.log').open('w') as log:subprocess.run(cmd,env=env,check=True,stdout=log,stderr=subprocess.STDOUT)
report=dict(result='BUILT_EXACT_STAGE_TRAFFIC_REFRESH_CORE',command=cmd,core_sha256=sha(out/'capture-host.dll'),baseline_core_sha256=r['core_sha256'],baseline_build_sha256=sha(baseline/'traffic-draw-camera-build-report.json'),baseline_parity_sha256=sha(baseline/'traffic-draw-camera-core-test-report.json'),failure_evidence_sha256=sha(proof),maintained_source_sha256=dict(r['maintained_source_sha256'],**{'traffic_rotation_refresh_capture.inc':sha(source/'traffic_rotation_refresh_capture.inc')}),staged_input_sha256={str(p.relative_to(staged)):sha(p) for p in staged.rglob('*') if p.is_file()},script_sha256=sha(Path(__file__)),game_logic_changed=False,full_scene_60fps=False,live_integration_verified=False)
(out/'traffic-refresh-build-report.json').write_text(json.dumps(report,indent=2));print(report['result'],report['core_sha256'])
