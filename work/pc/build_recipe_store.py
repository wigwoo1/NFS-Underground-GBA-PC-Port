from pathlib import Path
import os,hashlib,json,subprocess,shutil
here=Path(__file__).resolve().parent;out=Path(r'C:\NFSUG-Workspace\NFSUG-pc-recipe-store-tests');out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for name in ['recipe_store.c','recipe_store.h']:shutil.copy2(here/name,out/name)
args=['C:/msys64/mingw64/bin/gcc.exe','-O2','-Wall','-Wextra','-Werror','-shared',str(out/'recipe_store.c'),'-o',str(out/'recipe-store.dll')];env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','');subprocess.run(args,env=env,check=True)
r=dict(result='BUILT_BOUNDED_OWNED_RECIPE_STORE_TESTS_PENDING',command=args,dll_sha256=sha(out/'recipe-store.dll'),source_sha256={name:sha(here/name) for name in ['recipe_store.c','recipe_store.h']},script_sha256=sha(Path(__file__)),live_integration=False)
(out/'store-build-report.json').write_text(json.dumps(r,indent=2));print(r['result'],r['dll_sha256'])
