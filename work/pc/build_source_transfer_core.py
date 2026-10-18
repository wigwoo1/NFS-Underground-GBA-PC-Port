"""Build maintained transfer ABI over the verified owned-assembly core."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess
source=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');baseline=base/'NFSUG-pc-owned-assembly-core-tests';out=base/'NFSUG-pc-source-transfer-core';out.mkdir(exist_ok=True);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=argparse.ArgumentParser();p.add_argument('--reuse',action='store_true');args=p.parse_args();incs=['source_transfer_observer.inc','source_transfer_core_api.inc'];r=json.loads((baseline/'owned-core-build-report.json').read_text());parity=json.loads((baseline/'owned-core-test-report.json').read_text())
assert parity['result']=='PASS_OWNED_ASSEMBLY_CORE_PARITY' and parity['core_sha256']==r['core_sha256']==sha(baseline/'capture-host.dll')
for n,h in r['staged_input_sha256'].items():assert sha(baseline/'source'/n)==h,n
receipt=out/'source-transfer-build-report.json'
if args.reuse and receipt.exists():
 prior=json.loads(receipt.read_text())
 if prior['core_sha256']==sha(out/'capture-host.dll') and prior['baseline_build_sha256']==sha(baseline/'owned-core-build-report.json') and prior['abi_source_sha256']=={n:sha(source/n) for n in incs} and prior['script_sha256']==sha(Path(__file__)):
  for n,h in prior['staged_input_sha256'].items():assert sha(out/'source'/n)==h,n
  print('REUSED_VERIFIED_SOURCE_TRANSFER_CORE');raise SystemExit(0)
staged=out/'source';shutil.copytree(baseline/'source',staged,dirs_exist_ok=True)
for n in incs:shutil.copy2(source/n,staged/n)
for n,inc in [('observer.c',incs[0]),('nfsug_android_core.c',incs[1])]:
 with (staged/n).open('a') as f:f.write('\n#include "'+inc+'"\n')
cmd=[a.replace(str(baseline/'source'),str(staged)).replace(str(baseline/'capture-host.dll'),str(out/'capture-host.dll')) for a in r['command']];env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
with (out/'build.log').open('w') as log:subprocess.run(cmd,env=env,check=True,stdout=log,stderr=subprocess.STDOUT)
b=dict(result='BUILT_MAINTAINED_SOURCE_TRANSFER_CORE',command=cmd,baseline_core_sha256=r['core_sha256'],baseline_build_sha256=sha(baseline/'owned-core-build-report.json'),baseline_parity_sha256=sha(baseline/'owned-core-test-report.json'),core_sha256=sha(out/'capture-host.dll'),abi_source_sha256={n:sha(source/n) for n in incs},staged_input_sha256={str(p.relative_to(staged)):sha(p) for p in staged.rglob('*') if p.is_file()},script_sha256=sha(Path(__file__)),game_logic_changed=False,full_scene_60fps=False)
receipt.write_text(json.dumps(b,indent=2));(out/'owned-core-build-report.json').write_text(json.dumps(b,indent=2));print(json.dumps({k:v for k,v in b.items() if k not in ['command','staged_input_sha256']},indent=2))
