from pathlib import Path
import os,json,hashlib,subprocess,shutil
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');prior=base/'NFSUG-pc-region-mask-edges-tests';out=base/'NFSUG-pc-writer-gpu-tests';out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
b=json.loads((prior/'recipe-gpu-build-report.json').read_text());w=json.loads((base/'NFSUG-pc-recipe-writer-tests/writer-build-report.json').read_text())
for receipt in [b,w]:
 for p,h in receipt['source_sha256'].items():assert sha(p)==h,p
for p,h in b['staged_sha256'].items():assert sha(p)==h,p
for name in ['recipe-regions.dll','region-build-report.json','sky_composition.inc']:shutil.copyfile(prior/name,out/name);assert sha(prior/name)==sha(out/name)
staged_old=prior/'scene_gpu_mask_edges.c';s=staged_old.read_text();needle='GLuint coverage_program;';assert s.count(needle)==1;s=s.replace(needle,needle+'GLuint writer_program,writer_map_texture,writer_shade_texture;');needle='if(g->coverage_program&&g->delete_program)';assert s.count(needle)==1;s=s.replace(needle,'if(g->writer_program&&g->delete_program)g->delete_program(g->writer_program);if(g->writer_map_texture)glDeleteTextures(1,&g->writer_map_texture);if(g->writer_shade_texture)glDeleteTextures(1,&g->writer_shade_texture);'+needle);s+='\n#include "writer_gpu.inc"\n';staged=out/'scene_gpu_writer.c';staged.write_text(s)
args=[a.replace(str(staged_old),str(staged)).replace(str(prior/'recipe-gpu.dll'),str(out/'recipe-gpu.dll')) for a in b['command']];args[1:1]=[str(here/'writer_address_map.c')];env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','');subprocess.run(args,env=env,check=True)
b.update(result='BUILT_ORIGINAL_WRITER_RAW_TEXTURE_GPU_TESTS_PENDING',dll_sha256=sha(out/'recipe-gpu.dll'),command=args,script_sha256=sha(Path(__file__)),previous_gpu_sha256=sha(prior/'recipe-gpu.dll'),previous_receipt_sha256=sha(prior/'recipe-gpu-build-report.json'))
for n in ['writer_address_map.c','writer_address_map.h','recipe_writer.c','recipe_writer.h','writer_gpu.h','writer_gpu.inc']:b['source_sha256'][str(here/n)]=sha(here/n)
b['staged_sha256']={str(staged):sha(staged),str(out/'sky_composition.inc'):sha(out/'sky_composition.inc')};(out/'recipe-gpu-build-report.json').write_text(json.dumps(b,indent=2));print('STRICT_WRITER_ADDRESS_AND_GPU_BUILD_PASS',b['dll_sha256'])
