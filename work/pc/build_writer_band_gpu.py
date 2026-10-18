from pathlib import Path
import os,json,hashlib,subprocess,shutil
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');prior=base/'NFSUG-pc-writer-scene-tests';out=base/'NFSUG-pc-writer-band-tests';out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
b=json.loads((prior/'recipe-gpu-build-report.json').read_text())
for group in ['source_sha256','staged_sha256']:
 for p,h in b[group].items():assert sha(p)==h,p
assert sha(prior/'recipe-gpu.dll')==b['dll_sha256']
for name in ['recipe-regions.dll','region-build-report.json','sky_composition.inc']:shutil.copyfile(prior/name,out/name)
s=(here/'writer_gpu.inc').read_text();signature='int nf_pc_scene_gpu_render_writer(';assert s.count(signature)==1;s=s.replace(signature,'static int writer_band_internal(').replace('unsigned endpoint,unsigned index_mode){','unsigned endpoint,unsigned index_mode,unsigned band_top,unsigned band_bottom){')
s=s.replace('if(!g||g->owner','if(band_top>band_bottom||band_bottom>160||!g||g->owner')
s=s.replace('uniform vec2 viewport;','uniform vec2 displayBand;uniform vec2 viewport;')
anchor='h=int(viewport.y);vec2 st;';assert s.count(anchor)==1;s=s.replace(anchor,'h=int(viewport.y);int displayRow=(((h-py)*2-1)*80)/h;if(displayRow<int(displayBand.x)||displayRow>=int(displayBand.y))discard;vec2 st;')
anchor='g->uniform1i(g->uniform(g->writer_program,"endpoint"),(GLint)endpoint);';assert s.count(anchor)==1;s=s.replace(anchor,'g->uniform2f(g->uniform(g->writer_program,"displayBand"),(float)band_top,(float)band_bottom);'+anchor)
s+='''\n#include "writer_band_gpu.h"
int nf_pc_scene_gpu_render_writer(NFPCSceneGPU*g,const double*r,unsigned n,const unsigned b[4],const NFPCRecipeWriter*w,const NFPCWriterAddressMap*m,const void*p,size_t z,unsigned aw,unsigned ah,unsigned e,unsigned mode){return writer_band_internal(g,r,n,b,w,m,p,z,aw,ah,e,mode,0,160);}
int nf_pc_scene_gpu_render_writer_band(NFPCSceneGPU*g,const double*r,unsigned n,const unsigned b[4],const NFPCRecipeWriter*w,const NFPCWriterAddressMap*m,const void*p,size_t z,unsigned aw,unsigned ah,unsigned e,unsigned mode,unsigned top,unsigned bottom){return writer_band_internal(g,r,n,b,w,m,p,z,aw,ah,e,mode,top,bottom);}
'''
extension=out/'writer_band_generated.inc';extension.write_text(s)
old=prior/'scene_gpu_writer_scene.c';staged=out/'scene_gpu_writer_band.c';staged.write_text(old.read_text().replace('#include "writer_gpu.inc"','#include "writer_band_generated.inc"')+'\n#include "writer_scene_band_gpu.inc"\n')
args=[a.replace(str(old),str(staged)).replace(str(prior/'recipe-gpu.dll'),str(out/'recipe-gpu.dll')) for a in b['command']];env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','');subprocess.run(args,env=env,check=True)
b.update(result='BUILT_INTEGER_DISPLAY_BAND_WRITER_TESTS_PENDING',dll_sha256=sha(out/'recipe-gpu.dll'),command=args,script_sha256=sha(Path(__file__)),previous_gpu_sha256=sha(prior/'recipe-gpu.dll'),previous_receipt_sha256=sha(prior/'recipe-gpu-build-report.json'))
for n in ['writer_band_gpu.h','writer_scene_band_gpu.inc']:b['source_sha256'][str(here/n)]=sha(here/n)
b['staged_sha256']={str(staged):sha(staged),str(extension):sha(extension),str(out/'sky_composition.inc'):sha(out/'sky_composition.inc')};(out/'recipe-gpu-build-report.json').write_text(json.dumps(b,indent=2));print('STRICT_INTEGER_DISPLAY_BAND_BUILD_PASS',b['dll_sha256'])
