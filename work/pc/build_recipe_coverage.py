from pathlib import Path
import os,json,hashlib,subprocess
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-recipe-coverage-tests';out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
b=json.loads((base/'NFSUG-pc-retention-tests/retention-build-report.json').read_text())
for n in ['source_frame.c','source_frame.h','source_retention.c','source_retention.h']:assert sha(here/n)==b['source_sha256'][n],n
args=['C:/msys64/mingw64/bin/gcc.exe','-O2','-Wall','-Wextra','-Werror','-ffp-contract=off','-shared',str(here/'source_frame.c'),str(here/'recipe_coverage.c'),'-o',str(out/'recipe-coverage.dll')];env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','');subprocess.run(args,env=env,check=True)
r=dict(result='BUILT_RETAINED_EXACT_WRITER_COVERAGE_TESTS_PENDING',dll_sha256=sha(out/'recipe-coverage.dll'),command=args,source_sha256={str(here/n):sha(here/n) for n in ['source_frame.c','source_frame.h','recipe_coverage.c','recipe_coverage.h']},baseline_receipt_sha256=sha(base/'NFSUG-pc-retention-tests/retention-build-report.json'),baseline_retention_sha256=sha(here/'source_retention.c'),script_sha256=sha(Path(__file__)),full_scene_60fps=False)
(out/'coverage-build-report.json').write_text(json.dumps(r,indent=2));print(r['result'],r['dll_sha256'])
