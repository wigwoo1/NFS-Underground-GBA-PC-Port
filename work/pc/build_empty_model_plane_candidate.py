"""Isolated model-empty-plane candidate; existing strict model API unchanged."""
from pathlib import Path
import hashlib,json,os,subprocess
source=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-empty-model-plane-tests';out.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();receipt=out/'before/scene-build-report.json';r=json.loads(receipt.read_text())
for n,h in r['source_sha256'].items():assert sha(out/'before'/n if n in ('source_scene.c','build_source_scene.py') else source/n)==h,n
s=(out/'before/source_scene.c').read_text();s='#include "empty_model_plane.h"\n'+s
a='if(!(c->model?nf_pc_model_mesh_plane(c->model,i,p):nf_pc_world_mesh_plane(c->world,i,p)))goto owner_done;'
b='if(!(c->model?nf_pc_model_mesh_plane(c->model,i,p):nf_pc_world_mesh_plane(c->world,i,p))&&!(c->model&&nf_pc_empty_model_plane((const float*)c->vertices+i*15,p)))goto owner_done;'
assert s.count(a)==1;s=s.replace(a,b,1);staged=out/'source_scene_empty_plane.c';staged.write_text(s)
adapter=r'''
#include "scene_internal.h"
#include "scene_gpu.h"
#include "empty_model_plane.h"
#include <string.h>
NFPC_API int nf_pc_test_empty_plane(const float*v,float*out){return nf_pc_empty_model_plane(v,out);}
NFPC_API int nf_pc_test_triangle_gpu(NFPCSceneGPU*g,NFPCScene*s,const float xy[6],unsigned w,unsigned h,unsigned aw,unsigned ah,void*out,size_t bytes){
 if(!g||!s||!xy||!out)return 0;
 NFPCSceneCommand saved=s->commands[0],command;uint64_t count=s->info[3];float vertices[15],plane[11]={0,0,0,0,1,0,0,0,0,0,0};static const unsigned char red[4]={255,0,0,255};memset(&command,0,sizeof(command));
 for(unsigned i=0;i<3;i++){vertices[i*5]=xy[i*2];vertices[i*5+1]=xy[i*2+1];vertices[i*5+2]=vertices[i*5+3]=0;vertices[i*5+4]=1;}
 command.info[1]=1;command.info[3]=command.info[4]=1;command.info[5]=3;command.info[10]=240;command.info[12]=command.info[14]=160;command.vertices=vertices;command.vertices_bytes=sizeof(vertices);command.planes=plane;command.image=red;
 s->commands[0]=command;s->info[3]=1;int ok=nf_pc_scene_gpu_draw_passes(g,s,w,h,aw,ah,4,out,bytes);s->commands[0]=saved;s->info[3]=count;return ok;
}
'''
(out/'gpu_test_adapter.c').write_text(adapter);dll=out/'source-scene-empty-plane.dll';cmd=[str(staged) if a==str(source/'source_scene.c') else str(dll) if a.endswith('source-scene.dll') else a for a in r['command']];assert str(staged) in cmd;cmd.insert(1,'-I'+str(source));cmd.insert(-6,str(out/'gpu_test_adapter.c'))
env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
with (out/'build.log').open('w') as log:subprocess.run(cmd,env=env,check=True,stdout=log,stderr=subprocess.STDOUT)
report=dict(result='BUILT_EMPTY_AXIS_MODEL_PLANE_CANDIDATE',dll_sha256=sha(dll),baseline_dll_sha256=sha(out/'before/source-scene.dll'),baseline_receipt_sha256=sha(receipt),helper_sha256=sha(source/'empty_model_plane.h'),staged_source_sha256=sha(staged),test_adapter_sha256=sha(out/'gpu_test_adapter.c'),script_sha256=sha(Path(__file__)),command=cmd,source_sha256=r['source_sha256'],vertices_or_order_changed=False,strict_model_plane_api_changed=False,full_scene_60fps=False)
(out/'empty-plane-build-report.json').write_text(json.dumps(report,indent=2));print(report['result'],report['dll_sha256'])
