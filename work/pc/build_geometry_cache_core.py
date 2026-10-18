"""Build optional guarded cache using pinned maintained transfer sources.

Separate output preserves the tested playable preview and maintained core.
The factory checks upstream receipts and patches only transfer dispatch/lifecycle.
"""
from pathlib import Path
import hashlib,json,os,shutil,subprocess
source=Path(__file__).resolve().parent
base=Path(r'C:\NFSUG-Workspace')
baseline=base/'NFSUG-pc-source-transfer-core'
out=base/'NFSUG-pc-geometry-cache-core';out.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((baseline/'source-transfer-build-report.json').read_text())
parity=json.loads((baseline/'source-transfer-core-test-report.json').read_text())
assert parity['result']=='PASS_SOURCE_TRANSFER_CORE_PARITY' and parity['core_sha256']==r['core_sha256']==sha(baseline/'capture-host.dll')
for n,h in r['staged_input_sha256'].items():assert sha(baseline/'source'/n)==h,n
for n,h in r['abi_source_sha256'].items():assert sha(source/n)==h,n
test_dir=base/'NFSUG-pc-geometry-cache-tests'
test=json.loads((test_dir/'geometry-cache-test-report.json').read_text())
assert test['result']=='PASS_GEOMETRY_PACKET_CACHE_COMPONENT'
for n,h in test['source_sha256'].items():assert sha(source/n)==h,n
staged=out/'source';shutil.copytree(baseline/'source',staged,dirs_exist_ok=True)
extras=['geometry_packet_cache.c','geometry_packet_cache.h','geometry_cache_observer.inc','geometry_cache_core_api.inc']
for n in extras:shutil.copy2(source/n,staged/n)
observer=staged/'observer.c';s=observer.read_text()
def replace(a,b):
 global s
 assert s.count(a)==1,a
 s=s.replace(a,b,1)
s='void nf_android_geometry_cache_reset(int);\n'+s
replace('void nf_android_observer_detach(void){','void nf_android_observer_detach(void){\n nf_android_geometry_cache_reset(1);')
replace('void nf_android_observer_reset(void){','void nf_android_observer_reset(void){\n nf_android_geometry_cache_reset(0);')
replace('if(!enabled){if(android_source_world)', 'if(!enabled){nf_android_geometry_cache_reset(0);if(android_source_world)')
replace('#include "source_transfer_observer.inc"', '#define nf_android_observer_source_world_take nf_android_observer_source_world_take_uncached\n#include "source_transfer_observer.inc"\n#undef nf_android_observer_source_world_take\n#include "geometry_cache_observer.inc"')
observer.write_text(s)
with (staged/'nfsug_android_core.c').open('a') as f:f.write('\n#include "geometry_cache_core_api.inc"\n')
cmd=[a.replace(str(baseline/'source'),str(staged)).replace(str(baseline/'capture-host.dll'),str(out/'capture-host.dll')) for a in r['command']]
cmd.insert(cmd.index(str(staged/'observer.c'))+1,str(staged/'geometry_packet_cache.c'))
env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
with (out/'build.log').open('w') as log:subprocess.run(cmd,env=env,check=True,stdout=log,stderr=subprocess.STDOUT)
b=dict(result='BUILT_OPTIONAL_GUARDED_GEOMETRY_CACHE_CORE',command=cmd,baseline_core_sha256=r['core_sha256'],baseline_build_sha256=sha(baseline/'source-transfer-build-report.json'),baseline_parity_sha256=sha(baseline/'source-transfer-core-test-report.json'),component_test_receipt_sha256=sha(test_dir/'geometry-cache-test-report.json'),core_sha256=sha(out/'capture-host.dll'),maintained_source_sha256={n:sha(source/n) for n in extras+list(r['abi_source_sha256'])},staged_input_sha256={str(p.relative_to(staged)):sha(p) for p in staged.rglob('*') if p.is_file()},script_sha256=sha(Path(__file__)),cache_default_enabled=False,game_logic_changed=False,full_scene_60fps=False)
(out/'geometry-cache-build-report.json').write_text(json.dumps(b,indent=2));(out/'owned-core-build-report.json').write_text(json.dumps(b,indent=2))
print(json.dumps({k:v for k,v in b.items() if k not in ['command','staged_input_sha256']},indent=2))
