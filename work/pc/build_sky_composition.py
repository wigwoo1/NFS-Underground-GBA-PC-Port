"""Build isolated no-clear sky submission; preserve verified sky diagnostic."""
from pathlib import Path
import os,json,subprocess,hashlib
here=Path(__file__).resolve().parent
base=Path(r'C:\NFSUG-Workspace')
baseline=base/'NFSUG-pc-scene-tests'
out=base/'NFSUG-pc-sky-composition-tests';out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
receipt=json.loads((baseline/'scene-build-report.json').read_text())
for name,digest in receipt['source_sha256'].items():assert sha(here/name)==digest,name
def replace(text,a,b):
 assert text.count(a)==1,a
 return text.replace(a,b,1)
extension=(here/'sky_gpu.inc').read_text()
extension=replace(extension,'#include "sky_gpu.h"','#include "sky_composition.h"')
extension=replace(extension,'int nf_pc_scene_gpu_draw_sky(', 'static int sky_submit(')
extension=replace(extension,'void*out,size_t bytes){','void*out,size_t bytes,int overlay){')
extension=replace(extension,'||!out||count>64u*1024*1024||bytes<count',
 '||count>64u*1024*1024||(!overlay&&(!out||bytes<count))||(overlay&&(!g->target||g->width!=width||g->height!=height))')
extension=replace(extension,'glClearColor(0,0,0,0);glClear(GL_COLOR_BUFFER_BIT);',
 'if(!overlay){glClearColor(0,0,0,0);glClear(GL_COLOR_BUFFER_BIT);}')
extension=replace(extension,'glEnd();glFinish();glPixelStorei(GL_PACK_ALIGNMENT,1);glReadPixels(0,0,width,height,GL_RGBA,GL_UNSIGNED_BYTE,out);',
 'glEnd();if(!overlay){glFinish();glPixelStorei(GL_PACK_ALIGNMENT,1);glReadPixels(0,0,width,height,GL_RGBA,GL_UNSIGNED_BYTE,out);}')
extension+='''
/* Submission leaves the existing target intact outside the covered sky band.
   No target allocation, clear, glFinish, readback, or game-core callback. */
NFPC_API int nf_pc_scene_gpu_render_sky(NFPCSceneGPU*g,const void*a,size_t an,const void*b,size_t bn,double weight,const void*p,size_t pn,unsigned w,unsigned h,unsigned aw,unsigned ah,unsigned top,unsigned bottom){return sky_submit(g,a,an,b,bn,weight,p,pn,w,h,aw,ah,top,bottom,NULL,0,1);}
int nf_pc_scene_gpu_draw_sky(NFPCSceneGPU*g,const void*a,size_t an,const void*b,size_t bn,double weight,const void*p,size_t pn,unsigned w,unsigned h,unsigned aw,unsigned ah,unsigned top,unsigned bottom,void*out,size_t n){return sky_submit(g,a,an,b,bn,weight,p,pn,w,h,aw,ah,top,bottom,out,n,0);}
/* Readback is intentionally a separate diagnostic operation. */
NFPC_API int nf_pc_scene_gpu_read_target(NFPCSceneGPU*g,void*out,size_t n){
 if(!g||g->owner!=GetCurrentThreadId()||!g->target||!out||n<(size_t)g->width*g->height*4){error("Read target/thread");return 0;}
 HDC dc=wglGetCurrentDC();HGLRC old=wglGetCurrentContext();if(!wglMakeCurrent(g->dc,g->context))return 0;
 g->bind(FRAMEBUFFER,g->fbo);glPixelStorei(GL_PACK_ALIGNMENT,1);glReadPixels(0,0,g->width,g->height,GL_RGBA,GL_UNSIGNED_BYTE,out);int ok=glGetError()==GL_NO_ERROR;g->bind(FRAMEBUFFER,0);wglMakeCurrent(dc,old);return ok;
}
'''
inc=out/'sky_composition.inc';inc.write_text(extension)
text=(here/'scene_gpu.c').read_text()
text=replace(text,'GLuint input,palette,target,fbo,program,background,retention,hud,hudcopy;',
 'GLuint input,palette,target,fbo,program,background,retention,hud,hudcopy;GLuint sky_program,sky_upper;')
text=replace(text,'if(g->hud&&g->delete_program)',
 'if(g->sky_program&&g->delete_program)g->delete_program(g->sky_program);if(g->sky_upper)glDeleteTextures(1,&g->sky_upper);if(g->hud&&g->delete_program)')
text+='\n#include "sky_composition.inc"\n'
staged=out/'scene_gpu_sky.c';staged.write_text(text)
args=[arg.replace(str(here/'scene_gpu.c'),str(staged)).replace(str(baseline/'source-scene.dll'),str(out/'source-sky-gpu.dll')) for arg in receipt['command']]
args.insert(1,'-I'+str(here));env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','');subprocess.run(args,env=env,check=True)
r=dict(result='BUILT_ISOLATED_SKY_COMPOSITION_TESTS_PENDING',command=args,dll_sha256=sha(out/'source-sky-gpu.dll'),baseline_receipt_sha256=sha(baseline/'scene-build-report.json'),baseline_gpu_source_sha256=sha(here/'scene_gpu.c'),staged_gpu_source_sha256=sha(staged),staged_extension_sha256=sha(inc),extension_sha256={name:sha(here/name) for name in ['sky_gpu.h','sky_gpu.inc','sky_composition.h']},script_sha256=sha(Path(__file__)),baseline_source_sha256=receipt['source_sha256'],shipping_packages_changed=False,full_scene_60fps=False)
(out/'sky-gpu-build-report.json').write_text(json.dumps(r,indent=2));print(r['result'],r['dll_sha256'])
