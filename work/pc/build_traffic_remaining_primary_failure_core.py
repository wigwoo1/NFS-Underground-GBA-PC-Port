"""Read-only producer failure snapshot over the verified draw-camera candidate."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess
source=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');baseline=base/'NFSUG-pc-traffic-rotation-draw-camera-core';out=base/'NFSUG-pc-traffic-remaining-primary-failure-core';out.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();r=json.loads((baseline/'traffic-draw-camera-build-report.json').read_text());t=json.loads((baseline/'traffic-draw-camera-milestone-report.json').read_text())
assert t['result']=='VERIFIED_PARTIAL_TRAFFIC_PRODUCER_RECOVERY' and t['core_sha256']==r['core_sha256']==sha(baseline/'capture-host.dll')
for n,h in r['staged_input_sha256'].items():assert sha(baseline/'source'/n)==h,n
for n,h in r['maintained_source_sha256'].items():assert sha(source/n)==h,n
staged=out/'source';shutil.copytree(baseline/'source',staged,dirs_exist_ok=True);extras=['first_model_failure_observer.inc','first_model_failure_core_api.inc','traffic_remaining_primary_failure_observer.inc','traffic_remaining_failure_core_api.inc']
for n in extras:shutil.copy2(source/n,staged/n)
p=staged/'traffic_rotation_draw_capture.inc';s=p.read_text();a='failed:nf_traffic_pending.active=0;';assert s.count(a)==1;s=s.replace(a,'failed:nf_traffic_failure_event(cpu,pc,reason);nf_traffic_pending.active=0;',1)
s=s.replace('unsigned*r=(unsigned*)cpu->gprs,frame=c->frameCounter(c);','unsigned*r=(unsigned*)cpu->gprs,frame=c->frameCounter(c),reason=0;')
# Attach a reason to the four existing failure branches without changing their conditions.
parts=s.split('goto failed;');assert len(parts)==5
s=parts[0]+'{reason=1;goto failed;}'+parts[1]+'{reason=2;goto failed;}'+parts[2]+'{reason=3;goto failed;}'+parts[3]+'{reason=4;goto failed;}'+parts[4]
s=s.replace('static void nf_traffic_reset(void){','static void nf_traffic_reset(void){nf_traffic_failure_reset();',1);p.write_text(s)
p=staged/'camera/live_scene.h';s=p.read_text();a='static void live_scene_bad(void){if(!live_scene_first_bad[0]){';assert s.count(a)==1;s=s.replace(a,a+'nf_first_model_failure_capture();nf_traffic_remaining_freeze();',1);p.write_text(s)
p=staged/'observer.c';s=p.read_text();s='struct ARMCore;\nvoid nf_first_model_failure_capture(void);\nvoid nf_first_model_failure_reset(void);\nvoid nf_traffic_failure_reset(void);\nvoid nf_traffic_failure_event(struct ARMCore*,unsigned,unsigned);\nvoid nf_traffic_remaining_freeze(void);\n'+s
for a in ['void nf_android_observer_reset(void){','void nf_android_observer_detach(void){']:
 assert s.count(a)==1;s=s.replace(a,a+'nf_first_model_failure_reset();nf_traffic_failure_reset();',1)
s+='\n#include "first_model_failure_observer.inc"\n#include "traffic_remaining_primary_failure_observer.inc"\n';p.write_text(s)
with (staged/'nfsug_android_core.c').open('a') as f:f.write('\n#include "first_model_failure_core_api.inc"\n#include "traffic_remaining_failure_core_api.inc"\n')
cmd=[a.replace(str(baseline/'source'),str(staged)).replace(str(baseline/'capture-host.dll'),str(out/'capture-host.dll')) for a in r['command']];env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
with (out/'build.log').open('w') as log:subprocess.run(cmd,env=env,check=True,stdout=log,stderr=subprocess.STDOUT)
b=dict(result='BUILT_READONLY_TRAFFIC_PRIMARY_FAILURE_CORE',command=cmd,core_sha256=sha(out/'capture-host.dll'),baseline_core_sha256=r['core_sha256'],baseline_build_sha256=sha(baseline/'traffic-draw-camera-build-report.json'),baseline_milestone_sha256=sha(baseline/'traffic-draw-camera-milestone-report.json'),maintained_source_sha256={n:sha(source/n) for n in list(r['maintained_source_sha256'])+extras},staged_input_sha256={str(p.relative_to(staged)):sha(p) for p in staged.rglob('*') if p.is_file()},script_sha256=sha(Path(__file__)),capture_validation_changed=False,game_logic_changed=False,full_scene_60fps=False)
(out/'traffic-remaining-primary-failure-build-report.json').write_text(json.dumps(b,indent=2));(out/'owned-core-build-report.json').write_text(json.dumps(b,indent=2));print(b['result'],b['core_sha256'])
