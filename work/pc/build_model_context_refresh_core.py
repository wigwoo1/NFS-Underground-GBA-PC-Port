"""Diagnostic/control and optional guarded source-context refresh handoff."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess
source=Path(__file__).resolve().parent;base=Path(r"C:\NFSUG-Workspace")
p=argparse.ArgumentParser();p.add_argument('--handoff',action='store_true');args=p.parse_args()
baseline=base/'NFSUG-pc-scene-rejection-core';out=base/('NFSUG-pc-model-context-handoff' if args.handoff else 'NFSUG-pc-model-context-control');out.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((baseline/'scene-rejection-build-report.json').read_text());t=json.loads((baseline/'scene-rejection-core-test-report.json').read_text())
assert t['result']=='PASS_READONLY_SCENE_REJECTION_CORE_PARITY' and t['core_sha256']==r['core_sha256']==sha(baseline/'capture-host.dll')
for n,h in r['staged_input_sha256'].items():assert sha(baseline/'source'/n)==h,n
for n,h in r['maintained_source_sha256'].items():assert sha(source/n)==h,n
prerequisites={}
if args.handoff:
 helper=base/'NFSUG-pc-model-context-helper-tests/context-handoff-helper-test-report.json';proof=base/'NFSUG-pc-model-context-control/probe/context-refresh-probe-report.json'
 hr=json.loads(helper.read_text());pr=json.loads(proof.read_text())
 assert hr['result']=='PASS_GUARDED_ONE_REFRESH_CONTEXT_HANDOFF' and hr['source_sha256']==sha(source/'model_context_refresh.inc') and hr['script_sha256']==sha(source/'test_model_context_refresh.py')
 assert pr['result']=='PASS_CONTEXT_FAILURE_IS_ONLY_ONE_REFRESH_AGE' and pr['maintained_probe_sha256']==sha(source/'probe_model_context_refresh.py') and pr['build_receipt_sha256']==sha(base/'NFSUG-pc-model-context-control/context-refresh-build-report.json')
 prerequisites={'helper_test_receipt_sha256':sha(helper),'control_proof_receipt_sha256':sha(proof)}
staged=out/'source';shutil.copytree(baseline/'source',staged,dirs_exist_ok=True)
extras=['model_context_refresh.inc','model_context_diag_observer.inc','model_context_diag_core_api.inc']
for n in extras:shutil.copy2(source/n,staged/n)
h=staged/'camera/live_visibility.h';s=h.read_text()
a='static int live_native_context_matches(';assert s.count(a)==1;s=s.replace(a,'#include "../model_context_refresh.inc"\n'+a,1)
a='if(!live_native_context_matches(context,object,live_scene_epoch,live_scene.serial,c->frameCounter(c))){live_native_model_assembly_stats[2]++;return 0;}'
b='if(!live_native_context_matches(context,object,live_scene_epoch,live_scene.serial,c->frameCounter(c))){nf_context_rejection_capture(context,object,live_scene_epoch,live_scene.serial,c->frameCounter(c));live_native_model_assembly_stats[2]++;return 0;}'
assert s.count(a)==1;s=s.replace(a,b,1)
a='if(a&&b&&original_size==native_size&&!memcmp(original,native,original_size))live_native_context_extract_stats[1]++;'
b='if(a&&b&&original_size==native_size&&!memcmp(original,native,original_size)){live_native_context_extract_stats[1]++;\n#ifdef NF_MODEL_CONTEXT_REFRESH_HANDOFF\n nf_context_refresh_commit(cpu->gprs[0],live_scene.object,live_scene_epoch,live_scene.serial,frame);\n#endif\n }'
assert s.count(a)==1;s=s.replace(a,b,1);h.write_text(s)
for n,inc in [('observer.c',extras[1]),('nfsug_android_core.c',extras[2])]:
 with (staged/n).open('a') as f:f.write('\n#include "'+inc+'"\n')
cmd=[a.replace(str(baseline/'source'),str(staged)).replace(str(baseline/'capture-host.dll'),str(out/'capture-host.dll')) for a in r['command']]
if args.handoff:cmd.insert(1,'-DNF_MODEL_CONTEXT_REFRESH_HANDOFF')
env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
with (out/'build.log').open('w') as log:subprocess.run(cmd,env=env,check=True,stdout=log,stderr=subprocess.STDOUT)
b=dict(result='BUILT_MODEL_CONTEXT_HANDOFF' if args.handoff else 'BUILT_MODEL_CONTEXT_CONTROL',handoff_enabled=args.handoff,command=cmd,baseline_core_sha256=r['core_sha256'],core_sha256=sha(out/'capture-host.dll'),baseline_build_sha256=sha(baseline/'scene-rejection-build-report.json'),baseline_parity_sha256=sha(baseline/'scene-rejection-core-test-report.json'),maintained_source_sha256={n:sha(source/n) for n in list(r['maintained_source_sha256'])+extras},staged_input_sha256={str(p.relative_to(staged)):sha(p) for p in staged.rglob('*') if p.is_file()},script_sha256=sha(Path(__file__)),prerequisites=prerequisites,game_logic_changed=False,full_scene_60fps=False)
(out/'context-refresh-build-report.json').write_text(json.dumps(b,indent=2));(out/'owned-core-build-report.json').write_text(json.dumps(b,indent=2));print(json.dumps({k:v for k,v in b.items() if k not in ['command','staged_input_sha256','maintained_source_sha256']},indent=2))
