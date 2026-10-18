from pathlib import Path
import os,json,hashlib,subprocess,shutil
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');prior=base/'NFSUG-pc-writer-gpu-tests';out=base/'NFSUG-pc-writer-scene-tests';out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
b=json.loads((prior/'recipe-gpu-build-report.json').read_text())
for group in ['source_sha256','staged_sha256']:
 for p,h in b[group].items():assert sha(p)==h,p
assert sha(prior/'recipe-gpu.dll')==b['dll_sha256']
for name in ['recipe-regions.dll','region-build-report.json','sky_composition.inc']:shutil.copyfile(prior/name,out/name)
old=prior/'scene_gpu_writer.c';staged=out/'scene_gpu_writer_scene.c';staged.write_text(old.read_text()+'\n#include "writer_scene_gpu.inc"\n')
args=[a.replace(str(old),str(staged)).replace(str(prior/'recipe-gpu.dll'),str(out/'recipe-gpu.dll')) for a in b['command']];env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','');subprocess.run(args,env=env,check=True)
b.update(result='BUILT_SCENE_OWNED_PALETTE_WRITER_BINDING_TESTS_PENDING',dll_sha256=sha(out/'recipe-gpu.dll'),command=args,script_sha256=sha(Path(__file__)),previous_gpu_sha256=sha(prior/'recipe-gpu.dll'),previous_receipt_sha256=sha(prior/'recipe-gpu-build-report.json'))
for n in ['writer_scene_gpu.h','writer_scene_gpu.inc']:b['source_sha256'][str(here/n)]=sha(here/n)
b['staged_sha256']={str(staged):sha(staged),str(out/'sky_composition.inc'):sha(out/'sky_composition.inc')};(out/'recipe-gpu-build-report.json').write_text(json.dumps(b,indent=2));print('STRICT_SCENE_PALETTE_WRITER_BUILD_PASS',b['dll_sha256'])
