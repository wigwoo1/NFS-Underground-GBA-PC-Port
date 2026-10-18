from pathlib import Path
import json,hashlib,os,subprocess,shutil
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');prior=base/'NFSUG-pc-region-mask-tests';out=base/'NFSUG-pc-region-mask-edges-tests';out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
b=json.loads((prior/'recipe-gpu-build-report.json').read_text())
for key in ['source_sha256','staged_sha256']:
 for p,h in b[key].items():assert sha(p)==h,p
for name in ['recipe-regions.dll','region-build-report.json','sky_composition.inc']:shutil.copyfile(prior/name,out/name);assert sha(prior/name)==sha(out/name)
staged_old=prior/'scene_gpu_mask.c';source=staged_old.read_text();needle='#include "coverage_mask_gpu.inc"';assert source.count(needle)==1;source=source.replace(needle,'#include "coverage_mask_edges_gpu.inc"');staged=out/'scene_gpu_mask_edges.c';staged.write_text(source)
args=[a.replace(str(staged_old),str(staged)).replace(str(prior/'recipe-gpu.dll'),str(out/'recipe-gpu.dll')) for a in b['command']];env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','');subprocess.run(args,env=env,check=True)
b.update(result='BUILT_DIRECT_PROJECTIVE_EDGE_MASK_TESTS_PENDING',dll_sha256=sha(out/'recipe-gpu.dll'),command=args,script_sha256=sha(Path(__file__)),previous_gpu_sha256=sha(prior/'recipe-gpu.dll'),previous_receipt_sha256=sha(prior/'recipe-gpu-build-report.json'));b['source_sha256'][str(here/'coverage_mask_edges_gpu.inc')]=sha(here/'coverage_mask_edges_gpu.inc');b['staged_sha256']={str(staged):sha(staged),str(out/'sky_composition.inc'):sha(out/'sky_composition.inc')};(out/'recipe-gpu-build-report.json').write_text(json.dumps(b,indent=2));print('STRICT_DIRECT_EDGE_GPU_BUILD_PASS',b['dll_sha256'])
