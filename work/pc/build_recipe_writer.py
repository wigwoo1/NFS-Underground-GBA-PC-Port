from pathlib import Path
import json,hashlib,subprocess,os
here=Path(__file__).resolve().parent;out=Path(r'C:\NFSUG-Workspace\NFSUG-pc-recipe-writer-tests');out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
args=['C:/msys64/mingw64/bin/gcc.exe','-O2','-Wall','-Wextra','-Werror','-ffp-contract=off','-shared',str(here/'recipe_writer.c'),'-o',str(out/'recipe-writer.dll')];env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','');subprocess.run(args,env=env,check=True);r=dict(result='BUILT_OWNED_ORIGINAL_WRITER_SAMPLING_TESTS_PENDING',dll_sha256=sha(out/'recipe-writer.dll'),command=args,source_sha256={str(here/n):sha(here/n) for n in ['recipe_writer.c','recipe_writer.h','recipe_store.h']},script_sha256=sha(Path(__file__)),full_scene_60fps=False);(out/'writer-build-report.json').write_text(json.dumps(r,indent=2));print(r['result'],r['dll_sha256'])
