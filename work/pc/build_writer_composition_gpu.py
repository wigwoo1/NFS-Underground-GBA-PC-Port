from pathlib import Path
import json,hashlib,os,shutil,subprocess
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');prior=base/'NFSUG-pc-writer-band-tests';out=base/'NFSUG-pc-writer-composition-tests';out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
b=json.loads((prior/'recipe-gpu-build-report.json').read_text())
for group in ['source_sha256','staged_sha256']:
 for p,h in b[group].items():assert sha(p)==h,p
assert sha(prior/'recipe-gpu.dll')==b['dll_sha256']
for name in ['recipe-regions.dll','region-build-report.json','sky_composition.inc','writer_band_generated.inc']:shutil.copyfile(prior/name,out/name)
old=prior/'scene_gpu_writer_band.c';staged=out/'scene_gpu_writer_composition.c';s=old.read_text();anchor='static int render(';assert s.count(anchor)==1;s=s.replace(anchor,'static int draw_scene_source_writers(NFPCSceneGPU*,const NFPCScene*,unsigned,unsigned);\n'+anchor)
anchor='GLuint input,palette,target';assert s.count(anchor)==1;s=s.replace(anchor,'const NFPCSceneWriterDraw*scene_writer_draws;size_t scene_writer_count;int use_scene_writer_draws;'+anchor)
s='#include "writer_composition_gpu.h"\n'+s
s=s.replace('GLuint input,palette,target','GLuint retention_integer_reference;GLuint input,palette,target')
s=s.replace('if(g->retention&&g->delete_program)', 'if(g->retention_integer_reference&&g->delete_program)g->delete_program(g->retention_integer_reference);if(g->retention&&g->delete_program)')
s=s.replace('static int draw_scene_source_writers(NFPCSceneGPU*,const NFPCScene*,unsigned,unsigned);','static int draw_scene_source_writers(NFPCSceneGPU*,const NFPCScene*,unsigned,unsigned);\nstatic int retained_integer_reference(NFPCSceneGPU*,const NFPCScene*,unsigned,unsigned);')
start=s.index(' if(passes&2u)for(unsigned layer=0;layer<2;layer++)');end=s.index('\n glDisable(GL_SCISSOR_TEST);g->use_program(g->program);',start)
old_loop=s[start:end];s=s[:start]+' if((passes&2u)&&g->use_scene_writer_draws){if(!(g->use_scene_writer_draws==2?retained_integer_reference(g,scene,aw,ah):draw_scene_source_writers(g,scene,aw,ah)))goto done;}else '+old_loop.lstrip()+s[end:]
s+='\n#include "writer_composition_gpu.inc"\n#include "writer_composition_reference.inc"\n';staged.write_text(s)
args=[a.replace(str(old),str(staged)).replace(str(prior/'recipe-gpu.dll'),str(out/'recipe-gpu.dll')) for a in b['command']];args[1:1]=[str(here/'recipe_coverage.c')];env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','');subprocess.run(args,env=env,check=True)
b.update(result='BUILT_COMPLETE_SCENE_SOURCE_WRITER_STAGE_TESTS_PENDING',dll_sha256=sha(out/'recipe-gpu.dll'),command=args,script_sha256=sha(Path(__file__)),previous_gpu_sha256=sha(prior/'recipe-gpu.dll'),previous_receipt_sha256=sha(prior/'recipe-gpu-build-report.json'))
for n in ['writer_composition_gpu.h','writer_composition_gpu.inc','writer_composition_reference.inc','recipe_coverage.c','recipe_coverage.h']:b['source_sha256'][str(here/n)]=sha(here/n)
b['staged_sha256']={str(p):sha(p) for p in [staged,out/'sky_composition.inc',out/'writer_band_generated.inc']};(out/'recipe-gpu-build-report.json').write_text(json.dumps(b,indent=2));print('STRICT_SOURCE_WRITER_COMPOSITION_BUILD_PASS',b['dll_sha256'])
