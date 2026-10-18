"""Build opt-in bounded rotation trace over verified first-event diagnostics."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess
source=Path(__file__).resolve().parent;base=Path(r"C:\NFSUG-Workspace");baseline=base/'NFSUG-pc-first-model-failure-core';out=base/'NFSUG-pc-rotation-trace-v2-core';out.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();r=json.loads((baseline/'first-model-build-report.json').read_text());t=json.loads((baseline/'first-model-core-test-report.json').read_text())
assert t['result']=='PASS_FIRST_FAILED_MODEL_CORE_PARITY' and t['core_sha256']==r['core_sha256']==sha(baseline/'capture-host.dll')
for n,h in r['staged_input_sha256'].items():assert sha(baseline/'source'/n)==h,n
for n,h in r['maintained_source_sha256'].items():assert sha(source/n)==h,n
staged=out/'source';shutil.copytree(baseline/'source',staged,dirs_exist_ok=True);extras=['rotation_trace_v2_observer.inc','rotation_trace_v2_core_api.inc']
for n in extras:shutil.copy2(source/n,staged/n)
h=staged/'camera/live_scene.h';s=h.read_text();a='static void native_scene_event(struct ARMCore*cpu,unsigned pc){';assert s.count(a)==1;s=s.replace(a,a+'\n if(pc==0x08023452||pc==0x0806db14||pc==0x0806d9d8||pc==0x03002628||pc==0x030045e0||pc==0x03004770)nf_rotation_trace_event(cpu,pc);',1);h.write_text(s)
p=staged/'first_model_failure_observer.inc';s=p.read_text();a='void nf_first_model_failure_capture(void){';assert s.count(a)==1;s=s.replace(a,a+'nf_rotation_trace_freeze();',1);p.write_text(s)
p=staged/'observer.c';s=p.read_text();s='struct ARMCore;\nvoid nf_rotation_trace_event(struct ARMCore*,unsigned);\nvoid nf_rotation_trace_freeze(void);\nvoid nf_rotation_trace_reset(void);\n'+s
for a in ['void nf_android_observer_reset(void){','void nf_android_observer_detach(void){']:
 assert s.count(a)==1;s=s.replace(a,a+'nf_rotation_trace_reset();',1)
s+='\n#include "rotation_trace_v2_observer.inc"\n';p.write_text(s)
with (staged/'nfsug_android_core.c').open('a') as f:f.write('\n#include "rotation_trace_v2_core_api.inc"\n')
cmd=[a.replace(str(baseline/'source'),str(staged)).replace(str(baseline/'capture-host.dll'),str(out/'capture-host.dll')) for a in r['command']];env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
with (out/'build.log').open('w') as log:subprocess.run(cmd,env=env,check=True,stdout=log,stderr=subprocess.STDOUT)
b=dict(result='BUILT_OPT_IN_ROTATION_TRACE_V2_CORE',command=cmd,baseline_core_sha256=r['core_sha256'],core_sha256=sha(out/'capture-host.dll'),baseline_build_sha256=sha(baseline/'first-model-build-report.json'),baseline_parity_sha256=sha(baseline/'first-model-core-test-report.json'),maintained_source_sha256={n:sha(source/n) for n in list(r['maintained_source_sha256'])+extras},staged_input_sha256={str(p.relative_to(staged)):sha(p) for p in staged.rglob('*') if p.is_file()},script_sha256=sha(Path(__file__)),game_logic_changed=False,capture_validation_changed=False,full_scene_60fps=False)
(out/'rotation-trace-v2-build-report.json').write_text(json.dumps(b,indent=2));(out/'owned-core-build-report.json').write_text(json.dumps(b,indent=2));print(json.dumps({k:v for k,v in b.items() if k not in ['command','staged_input_sha256','maintained_source_sha256']},indent=2))
