"""Build read-only rejection exports over the verified guarded-cache core."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess
source=Path(__file__).resolve().parent;base=Path(r"C:\NFSUG-Workspace")
baseline=base/'NFSUG-pc-geometry-cache-core';out=base/'NFSUG-pc-scene-rejection-core';out.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((baseline/'geometry-cache-build-report.json').read_text());t=json.loads((baseline/'geometry-cache-core-test-report.json').read_text())
assert t['result']=='PASS_GUARDED_GEOMETRY_CACHE_CORE_PARITY' and r['core_sha256']==t['core_sha256']==sha(baseline/'capture-host.dll')
for n,h in r['staged_input_sha256'].items():assert sha(baseline/'source'/n)==h,n
for n,h in r['maintained_source_sha256'].items():assert sha(source/n)==h,n
staged=out/'source';shutil.copytree(baseline/'source',staged,dirs_exist_ok=True)
extras=['scene_rejection_observer.inc','scene_rejection_core_api.inc']
for n in extras:shutil.copy2(source/n,staged/n)
for n,inc in [('observer.c',extras[0]),('nfsug_android_core.c',extras[1])]:
 with (staged/n).open('a') as f:f.write('\n#include "'+inc+'"\n')
cmd=[a.replace(str(baseline/'source'),str(staged)).replace(str(baseline/'capture-host.dll'),str(out/'capture-host.dll')) for a in r['command']]
env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
with (out/'build.log').open('w') as log:subprocess.run(cmd,env=env,check=True,stdout=log,stderr=subprocess.STDOUT)
b=dict(result='BUILT_READONLY_SCENE_REJECTION_CORE',command=cmd,baseline_core_sha256=r['core_sha256'],core_sha256=sha(out/'capture-host.dll'),baseline_build_sha256=sha(baseline/'geometry-cache-build-report.json'),baseline_parity_sha256=sha(baseline/'geometry-cache-core-test-report.json'),maintained_source_sha256={n:sha(source/n) for n in list(r['maintained_source_sha256'])+extras},staged_input_sha256={str(p.relative_to(staged)):sha(p) for p in staged.rglob('*') if p.is_file()},script_sha256=sha(Path(__file__)),game_logic_changed=False,validation_policy_changed=False,full_scene_60fps=False)
(out/'scene-rejection-build-report.json').write_text(json.dumps(b,indent=2));(out/'owned-core-build-report.json').write_text(json.dumps(b,indent=2));print(json.dumps({k:v for k,v in b.items() if k not in ['command','staged_input_sha256']},indent=2))
