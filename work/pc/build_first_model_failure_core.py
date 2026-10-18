"""Build read-only first-event diagnostics over the verified handoff core."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess
source=Path(__file__).resolve().parent;base=Path(r"C:\NFSUG-Workspace");baseline=base/'NFSUG-pc-model-context-handoff';out=base/'NFSUG-pc-first-model-failure-core';out.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();r=json.loads((baseline/'context-refresh-build-report.json').read_text());t=json.loads((baseline/'context-refresh-core-test-report.json').read_text())
assert t['result']=='PASS_CONTEXT_REFRESH_HANDOFF_CORE_PARITY' and t['core_sha256']==r['core_sha256']==sha(baseline/'capture-host.dll')
for n,h in r['staged_input_sha256'].items():assert sha(baseline/'source'/n)==h,n
for n,h in r['maintained_source_sha256'].items():assert sha(source/n)==h,n
staged=out/'source';shutil.copytree(baseline/'source',staged,dirs_exist_ok=True);extras=['first_model_failure_observer.inc','first_model_failure_core_api.inc']
for n in extras:shutil.copy2(source/n,staged/n)
h=staged/'camera/live_scene.h';s=h.read_text();a='static void live_scene_bad(void){if(!live_scene_first_bad[0]){';assert s.count(a)==1;s=s.replace(a,a+'nf_first_model_failure_capture();',1);h.write_text(s)
p=staged/'observer.c';s=p.read_text();s='void nf_first_model_failure_capture(void);\nvoid nf_first_model_failure_reset(void);\n'+s
for a in ['void nf_android_observer_reset(void){','void nf_android_observer_detach(void){']:
 assert s.count(a)==1;s=s.replace(a,a+'nf_first_model_failure_reset();',1)
s+='\n#include "first_model_failure_observer.inc"\n';p.write_text(s)
with (staged/'nfsug_android_core.c').open('a') as f:f.write('\n#include "first_model_failure_core_api.inc"\n')
cmd=[a.replace(str(baseline/'source'),str(staged)).replace(str(baseline/'capture-host.dll'),str(out/'capture-host.dll')) for a in r['command']];env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
with (out/'build.log').open('w') as log:subprocess.run(cmd,env=env,check=True,stdout=log,stderr=subprocess.STDOUT)
b=dict(result='BUILT_READONLY_FIRST_MODEL_FAILURE_CORE',command=cmd,baseline_core_sha256=r['core_sha256'],core_sha256=sha(out/'capture-host.dll'),baseline_build_sha256=sha(baseline/'context-refresh-build-report.json'),baseline_parity_sha256=sha(baseline/'context-refresh-core-test-report.json'),maintained_source_sha256={n:sha(source/n) for n in list(r['maintained_source_sha256'])+extras},staged_input_sha256={str(p.relative_to(staged)):sha(p) for p in staged.rglob('*') if p.is_file()},script_sha256=sha(Path(__file__)),game_logic_changed=False,capture_validation_changed=False,full_scene_60fps=False)
(out/'first-model-build-report.json').write_text(json.dumps(b,indent=2));(out/'owned-core-build-report.json').write_text(json.dumps(b,indent=2));print(json.dumps({k:v for k,v in b.items() if k not in ['command','staged_input_sha256','maintained_source_sha256']},indent=2))
