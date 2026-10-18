"""Guarded missing traffic producer over the verified production handoff core."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess
source=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');baseline=base/'NFSUG-pc-model-context-handoff';out=base/'NFSUG-pc-traffic-rotation-core';out.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();r=json.loads((baseline/'context-refresh-build-report.json').read_text());t=json.loads((baseline/'context-refresh-core-test-report.json').read_text())
assert t['result']=='PASS_CONTEXT_REFRESH_HANDOFF_CORE_PARITY' and t['core_sha256']==r['core_sha256']==sha(baseline/'capture-host.dll')
for n,h in r['staged_input_sha256'].items():assert sha(baseline/'source'/n)==h,n
for n,h in r['maintained_source_sha256'].items():assert sha(source/n)==h,n
proof=base/'NFSUG-pc-rotation-trace-v3-core/traffic-writer-milestone-report.json';assert json.loads(proof.read_text())['result']=='PASS_CONFIRMED_TRAFFIC_ROTATION_WRITER'
staged=out/'source';shutil.copytree(baseline/'source',staged,dirs_exist_ok=True);extras=['traffic_rotation_pose.inc','traffic_rotation_capture.inc','traffic_rotation_core_api.inc']
for n in extras:shutil.copy2(source/n,staged/n)
h=staged/'camera/live_scene.h';s=h.read_text()
def replace(a,b):
 global s
 assert s.count(a)==1,a;s=s.replace(a,b,1)
replace('struct {unsigned address,frame;int32_t matrix[12];} rotations[16];','struct {unsigned address,frame;int32_t matrix[12];unsigned traffic,traffic_object,traffic_camera,traffic_serial;uint64_t traffic_epoch;int32_t traffic_cm[12],traffic_actual[9];} rotations[16];')
replace('static void native_scene_event(struct ARMCore*cpu,unsigned pc){','#include "../traffic_rotation_capture.inc"\nstatic void native_scene_event(struct ARMCore*cpu,unsigned pc){')
replace('static void native_scene_event(struct ARMCore*cpu,unsigned pc){\n if(!live_scene.assembly)return;','static void native_scene_event(struct ARMCore*cpu,unsigned pc){\n if(!live_scene.assembly)return;\n if(nf_traffic_event(cpu,pc))return;')
replace('live_scene.rotations[i].address=r[2];live_scene.rotations[i].frame=c->frameCounter(c);','live_scene.rotations[i].address=r[2];live_scene.rotations[i].frame=c->frameCounter(c);live_scene.rotations[i].traffic=0;')
replace('live_scene.rotations[i].frame<=frame){','live_scene.rotations[i].frame<=frame&&nf_traffic_rotation_valid(i,live_scene.camera,live_scene.object)){')
s=s.replace('live_scene_epoch++;','nf_traffic_reset();live_scene_epoch++;');h.write_text(s)
h=staged/'camera/live_visibility.h';s=h.read_text();a='live_scene.rotations[i].frame<=frame){';assert s.count(a)==1;s=s.replace(a,'live_scene.rotations[i].frame<=frame&&nf_traffic_rotation_valid(i,live_scene.camera,live_scene.object)){',1);h.write_text(s)
with (staged/'observer.c').open('a') as f:f.write('\nint nf_android_traffic_rotation_stats(uint64_t out[6]){if(!c||!out)return 0;memcpy(out,nf_traffic_stats,48);return 1;}\n')
with (staged/'nfsug_android_core.c').open('a') as f:f.write('\n#include "traffic_rotation_core_api.inc"\n')
cmd=[a.replace(str(baseline/'source'),str(staged)).replace(str(baseline/'capture-host.dll'),str(out/'capture-host.dll')) for a in r['command']];env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
with (out/'build.log').open('w') as log:subprocess.run(cmd,env=env,check=True,stdout=log,stderr=subprocess.STDOUT)
b=dict(result='BUILT_GUARDED_TRAFFIC_ROTATION_CORE',command=cmd,core_sha256=sha(out/'capture-host.dll'),baseline_core_sha256=r['core_sha256'],baseline_build_sha256=sha(baseline/'context-refresh-build-report.json'),baseline_parity_sha256=sha(baseline/'context-refresh-core-test-report.json'),producer_proof_sha256=sha(proof),maintained_source_sha256={n:sha(source/n) for n in list(r['maintained_source_sha256'])+extras},staged_input_sha256={str(p.relative_to(staged)):sha(p) for p in staged.rglob('*') if p.is_file()},script_sha256=sha(Path(__file__)),game_logic_changed=False,full_scene_60fps=False)
(out/'traffic-rotation-build-report.json').write_text(json.dumps(b,indent=2));(out/'owned-core-build-report.json').write_text(json.dumps(b,indent=2));print(b['result'],b['core_sha256'])

