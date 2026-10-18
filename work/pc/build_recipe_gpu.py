from pathlib import Path
import os,json,subprocess,hashlib
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');prior=base/'NFSUG-pc-sky-composition-tests';mesh=base/'NFSUG-pc-recipe-mesh-tests';out=base/'NFSUG-pc-recipe-gpu-tests';out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
r=json.loads((prior/'sky-gpu-build-report.json').read_text());assert sha(prior/'source-sky-gpu.dll')==r['dll_sha256'];assert sha(prior/'scene_gpu_sky.c')==r['staged_gpu_source_sha256'];assert sha(prior/'sky_composition.inc')==r['staged_extension_sha256']
for name,h in r['baseline_source_sha256'].items():assert sha(here/name)==h,name
mr=json.loads((mesh/'mesh-build-report.json').read_text())
for p,h in mr['source_sha256'].items():assert sha(p)==h,p
for name in ['mesh-test-report.json','material-test-report.json']:assert json.loads((mesh/name).read_text())['result'].startswith('PASS_')
(out/'sky_composition.inc').write_bytes((prior/'sky_composition.inc').read_bytes())
staged=out/'scene_gpu_recipe.c';staged.write_text((prior/'scene_gpu_sky.c').read_text()+'\n#include "recipe_gpu.inc"\n')
args=[a.replace(str(prior/'scene_gpu_sky.c'),str(staged)).replace(str(prior/'source-sky-gpu.dll'),str(out/'recipe-gpu.dll')) for a in r['command']]
args[1:1]=[str(here/'recipe_mesh.c'),str(here/'recipe_material.c')]
# recipe_mesh uses the geometry API types only, with no geometry module calls.
env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','');subprocess.run(args,env=env,check=True)
report=dict(result='BUILT_RECIPE_GPU_TESTS_PENDING',dll_sha256=sha(out/'recipe-gpu.dll'),command=args,source_sha256={str(here/n):sha(here/n) for n in ['recipe_gpu.inc','recipe_gpu.h','recipe_mesh.c','recipe_mesh.h','recipe_material.c','recipe_material.h']},staged_sha256={str(p):sha(p) for p in [staged,out/'sky_composition.inc']},baseline_receipt_sha256=sha(prior/'sky-gpu-build-report.json'),mesh_receipt_sha256=sha(mesh/'mesh-build-report.json'),script_sha256=sha(Path(__file__)),full_scene_60fps=False)
(out/'recipe-gpu-build-report.json').write_text(json.dumps(report,indent=2));print(report['result'],report['dll_sha256'])
