from pathlib import Path
import os,json,hashlib,subprocess
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');region=base/'NFSUG-pc-recipe-region-tests';gpu=base/'NFSUG-pc-recipe-gpu-tests';out=base/'NFSUG-pc-region-mask-tests';out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
r=json.loads((region/'region-build-report.json').read_text())
for p,h in r['source_sha256'].items():assert sha(p)==h,p
args=[a.replace(str(region/'recipe-regions.dll'),str(out/'recipe-regions.dll')) for a in r['command']];args[1:1]=[str(here/'region_mask.c')];subprocess.run(args,env=env,check=True);r.update(result='BUILT_PROJECTIVE_COVERAGE_MASK_RINGS_TESTS_PENDING',dll_sha256=sha(out/'recipe-regions.dll'),command=args,script_sha256=sha(Path(__file__)));r['source_sha256'].update({str(here/n):sha(here/n) for n in ['region_mask.c','region_mask.h']});(out/'region-build-report.json').write_text(json.dumps(r,indent=2))
g=json.loads((gpu/'recipe-gpu-build-report.json').read_text())
for key in ['source_sha256','staged_sha256']:
 for p,h in g[key].items():assert sha(p)==h,p
staged_old=gpu/'scene_gpu_recipe.c';source=staged_old.read_text();a='GLuint input,palette,target,fbo,program,background,retention,hud,hudcopy;';assert source.count(a)==1;source=source.replace(a,a+'GLuint coverage_program;');a='if(g->hud&&g->delete_program)';assert source.count(a)==1;source=source.replace(a,'if(g->coverage_program&&g->delete_program)g->delete_program(g->coverage_program);'+a);source+='\n#include "coverage_mask_gpu.inc"\n';staged=out/'scene_gpu_mask.c';staged.write_text(source);(out/'sky_composition.inc').write_bytes((gpu/'sky_composition.inc').read_bytes())
args=[a.replace(str(staged_old),str(staged)).replace(str(gpu/'recipe-gpu.dll'),str(out/'recipe-gpu.dll')) for a in g['command']];subprocess.run(args,env=env,check=True);g.update(result='BUILT_EXPLICIT_GPU_COVERAGE_MASK_TESTS_PENDING',dll_sha256=sha(out/'recipe-gpu.dll'),command=args,script_sha256=sha(Path(__file__)));g['source_sha256'].update({str(here/n):sha(here/n) for n in ['coverage_mask_gpu.inc','coverage_mask_gpu.h']});g['staged_sha256']={str(staged):sha(staged),str(out/'sky_composition.inc'):sha(out/'sky_composition.inc')};(out/'recipe-gpu-build-report.json').write_text(json.dumps(g,indent=2));print('STRICT_CPU_AND_GPU_MASK_BUILDS_PASS',r['dll_sha256'],g['dll_sha256'])
