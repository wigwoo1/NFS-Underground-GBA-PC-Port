"""Isolated PC candidate: enable the existing canonical RAM copy path only."""
from pathlib import Path
import os,json,hashlib,shutil,subprocess,difflib
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');baseline=base/'NFSUG-pc-owned-assembly-core-tests';out=base/'NFSUG-pc-direct-ram-core-tests';source=out/'source';out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
receipt=json.loads((baseline/'owned-core-build-report.json').read_text());assert sha(baseline/'capture-host.dll')==receipt['core_sha256']
for name,digest in receipt['staged_input_sha256'].items():assert sha(baseline/'source'/name)==digest
shutil.copytree(baseline/'source',source,dirs_exist_ok=True)
p=source/'observer.c';old=p.read_text(encoding='utf-8');needle='if(getenv("NF_TEST_DIRECT_CAPTURE_RAM"))';assert old.count(needle)==1
new=old.replace(needle,'if(1) /* PC canonical RAM copy; all other ranges retain bus reads. */',1);p.write_text(new,encoding='utf-8')
args=[arg.replace(str(baseline/'source'),str(source)).replace(str(baseline/'capture-host.dll'),str(out/'capture-host.dll')) for arg in receipt['command']]
env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
with (out/'build.log').open('w') as log:subprocess.run(args,env=env,check=True,stdout=log,stderr=subprocess.STDOUT)
inputs={str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file()}
assert all(inputs[name]==digest for name,digest in receipt['staged_input_sha256'].items() if name!='observer.c')
(out/'observer-direct-ram.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='owned/observer.c',tofile='direct-ram/observer.c')))
r=dict(result='BUILT_DIRECT_RAM_CANDIDATE_TESTS_PENDING',core_sha256=sha(out/'capture-host.dll'),baseline_core_sha256=sha(baseline/'capture-host.dll'),baseline_build_receipt_sha256=sha(baseline/'owned-core-build-report.json'),staged_input_sha256=inputs,command=args,script_sha256=sha(Path(__file__)),game_logic_changed=False,shipping_packages_modified=False,rom_copy_enabled=False,changed_functions=['native_surface_read'])
(out/'owned-core-build-report.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k not in ['command','staged_input_sha256']},indent=2))
