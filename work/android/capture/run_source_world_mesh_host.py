from pathlib import Path
import argparse,ctypes as C,hashlib,json,os,struct,subprocess
p=argparse.ArgumentParser()
for name in ('output','fixtures','table','jdk','gcc'):p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args();android=Path(__file__).resolve().parents[1];work=android.parent;a.output.mkdir(parents=True,exist_ok=True);fixtures=a.output/'fixtures';fixtures.mkdir(exist_ok=True);decoded=a.output/'decoded';decoded.mkdir(exist_ok=True)
u=lambda b,o:struct.unpack_from('<I',b,o)[0]
def sections(raw):return [raw[u(raw,36+i*12):u(raw,36+i*12)+u(raw,40+i*12)] for i in range(5)]
def packet(parts):
 out=bytearray(96);struct.pack_into('<8I',out,0,0x3150534e,1,0,5,1,10,11,0)
 for i,part in enumerate(parts):out+=bytes((-len(out))%8);at=len(out);out+=part;struct.pack_into('<3I',out,32+i*12,i+1,at,len(part))
 struct.pack_into('<I',out,8,len(out));return bytes(out)
base=sections((a.fixtures/'mode5.nsp').read_bytes());table=a.table.read_bytes();assert len(table)==131072
shapes=[ [(-30,-10,32),(30,-10,100),(5,0,100),(30,30,100),(-30,30,100)], [(-30,-10,100),(30,-10,100),(5,0,100),(30,30,100),(-30,30,100)], [(-30,-10,10),(30,-10,20),(5,0,15),(30,30,30),(-30,30,25)], [(-30,-10,64),(30,-10,64),(5,0,64),(30,30,64),(-30,30,64)] ]
records=[]
for mode in (9,10):
 for shape,points0 in enumerate(shapes):
  for reverse in (0,1):
   points=list(reversed(points0)) if reverse else points0;parts=base.copy();ids=bytearray(parts[4]);identity_end=8+u(ids,4)*20
   if len(ids)>identity_end:struct.pack_into("<d",ids,identity_end+8,0.0)
   parts[4]=bytes(ids);model=bytearray(parts[0]);struct.pack_into('<3d',model,24,120,80,100);struct.pack_into('<7d',model,48,0,0,0,0,0,0,1);parts[0]=bytes(model);n=len(points);raw=bytearray(288);struct.pack_into('<6I2i',raw,0,n,2,4,mode==10,0x08001000,0x02000002,123,-65)
   for i in range(n):struct.pack_into('<2i',raw,32+i*8,(i-2)*14932,(i%3-1)*20480)
   surface=struct.pack('<3I',n,4,2)+b''.join(struct.pack('<3d',*v) for v in points)+b''.join(struct.pack('<2d',(i-2)*14932/16384.0+123/(256.0*4),(i%3-1)*20480/16384.0-65/(512.0*2)) for i in range(n))+bytes([50,80,100,255])*8
   matrix=[16000 if reverse else 16384,0,0,0,16384,0,0,0,16384,0,0,0];camera=struct.pack("<2I12i",1,0x02001000,*matrix);metadata=bytes(range(8))+camera+raw;parts[1]=struct.pack('<2I',0x31444652,1)+surface+struct.pack('<4I',0x3149574e,1,mode,len(metadata))+metadata;parts[3]=struct.pack('<3I',0x314c464e,1,0)+table
   name=f'mode{mode}-shape{shape}-reverse{reverse}.nsp';(fixtures/name).write_bytes(packet(parts));records.append((name,parts[0],surface,bytes(raw),mode,struct.pack("<12i",*matrix)))
# Compile canonical camera, corrected clip, projection and triangulation helpers.
names=('rigid_motion.c','rigid_motion.h','road_near_clip.h','road_triangulate.h','road_near_attributes.c','road_near_attributes.h','road_source_attributes.h','road_corrected_clip.h','road_camera_continuous.c','road_near_continuous.c','road_point_project_continuous.c','road_source_ring.c');reference_hashes={}
for name in names:
 data=(work/'camera'/name).read_bytes();(a.output/name).write_bytes(data);reference_hashes[name]=hashlib.sha256(data).hexdigest()
wrapper='#include "rigid_motion.h"\n#include "road_near_clip.h"\n#include "road_triangulate.h"\n#include "road_source_attributes.h"\n#include <stdint.h>\n#include <string.h>\nextern int nf_road_camera_continuous(const double*,const int32_t*,double*);\nextern int nf_road_source_ring(const double*,unsigned,const NFRoadSourceAttributes*,const int32_t*,const int32_t*,const uint32_t*,double*,unsigned,unsigned*);\n__declspec(dllexport) int world_mesh_reference(const void*model,size_t model_bytes,const void*surface,size_t surface_bytes,unsigned affine,const NFRoadSourceAttributes*raw,const uint32_t*table,const int32_t*matrix,double*camera,float*out,unsigned capacity,unsigned*written){\n const uint8_t*m=model,*s=surface;uint32_t n;memcpy(&n,s,4);double projection[3];memcpy(projection,m+24,24);int32_t params[3];for(int k=0;k<3;k++)params[k]=(int32_t)projection[k];double world[32][3],projected[64][5];memcpy(world,s+12,n*24);for(unsigned i=0;i<n;i++)if(!nf_road_camera_continuous(world[i],matrix,camera+i*3))return 0;unsigned amount;if(!nf_road_source_ring(&world[0][0],n,raw,matrix,params,table,&projected[0][0],64,&amount))return 0;RoadVertex vertices[64],triangles[192];\n for(unsigned i=0;i<amount;i++){double*q=projected[i];if(q[2]<=0)return 0;double r=affine?65536:q[2];vertices[i]=(RoadVertex){{q[0],q[1],16777216.0/q[2]},q[3]/(r*(1u<<raw->shift)*.5)+raw->offsets[0]/(256.0*(1u<<raw->shift)),q[4]/(r*raw->stored_height*.5)+raw->offsets[1]/(256.0*raw->stored_height)};}\n unsigned count=road_triangulate(vertices,amount,triangles);if(count>capacity)return 0;for(unsigned i=0;i<count;i++){double q=affine?1:1/triangles[i].p.z;out[i*5]=triangles[i].p.x;out[i*5+1]=triangles[i].p.y;out[i*5+2]=triangles[i].u*q;out[i*5+3]=triangles[i].v*q;out[i*5+4]=q;}*written=count;return 1;\n}\n'
(a.output/'source_world_reference.c').write_text(wrapper);dll=a.output/'source-world-reference.dll';env=os.environ.copy();env['PATH']=str(a.gcc.parent)+os.pathsep+env['PATH']
def run(cmd):
 r=subprocess.run(list(map(str,cmd)),capture_output=True,text=True,env=env)
 if r.returncode:print(r.stdout+r.stderr);r.check_returncode()
 return r.stdout
run([a.gcc,'-O2','-shared','-I'+str(a.output),a.output/'source_world_reference.c',*[a.output/n for n in names if n.endswith('.c')],'-lm','-o',dll]);classes=a.output/'classes';classes.mkdir(exist_ok=True);files=[android/'java/org/codex/nfsugpreview'/(n+'.java') for n in ('NativeScenePacket','NativeModelMesh','NativeWorldScene','NativeRoadAttributes','NativeRoadClip','NativeWorldMesh','NativeRoadCamera','NativeRoadProjection')]+[android/'tests/org/codex/nfsugpreview/CorrectedWorldMeshTest.java'];run([a.jdk/'bin/javac.exe','--release','8','-d',classes,*files]);stdout=run([a.jdk/'bin/java.exe','-cp',classes,'org.codex.nfsugpreview.CorrectedWorldMeshTest',fixtures,decoded]);print(stdout,flush=True)
os.add_dll_directory(str(a.gcc.parent));lib=C.CDLL(str(dll));fn=lib.world_mesh_reference;fn.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p,C.POINTER(C.c_double),C.POINTER(C.c_float),C.c_uint,C.POINTER(C.c_uint)];fn.restype=C.c_int;maximum=0;triangles=empty=0
for name,model,surface,raw,mode,matrix in records:
 n=u(surface,0);camera=(C.c_double*(n*3))();mesh=(C.c_float*960)();count=C.c_uint();assert fn(model,len(model),surface,len(surface),mode==10,raw,table,matrix,camera,mesh,192,C.byref(count)),name;jm=(decoded/(name+'.mesh')).read_bytes();jc=(decoded/(name+'.camera')).read_bytes();assert len(jm)==count.value*20 and len(jc)==n*24,name
 for i,value in enumerate(struct.unpack('<'+str(n*3)+'d',jc)):assert abs(value-camera[i])<=1e-9*max(1,abs(camera[i]))
 for i,value in enumerate(struct.unpack('<'+str(count.value*5)+'f',jm)):
  error=abs(value-mesh[i]);maximum=max(maximum,error);assert error<=2e-6*max(1,abs(mesh[i])),(name,i,value,mesh[i])
 triangles+=count.value//3;empty+=count.value==0
report={'result':'PASS_SOURCE_WORLD_MESH_C_PARITY','meshes':len(records),'triangles':triangles,'empty_meshes':empty,'max_float_difference':maximum,'reference_source_sha256':reference_hashes,'source_sha256':{str(f.relative_to(android)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'java_stdout':stdout.strip(),'scope':'Synthetic raw source-camera modes9/10 complete mesh preparation only; draw-plan GPU guard retained'};(a.output/'source-world-mesh-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
