"""Independent parity with existing PC C rigid transform and near clipping."""
from pathlib import Path
import argparse,ctypes as C,hashlib,json,os,struct,subprocess
p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);p.add_argument("--samples",type=Path,required=True);p.add_argument("--jdk",type=Path,required=True);a=p.parse_args()
source=Path(__file__).resolve().parent;android=source.parent;work=android.parent;a.output.mkdir(exist_ok=True,parents=True);models=a.output/"models";models.mkdir(exist_ok=True);classes=a.output/"classes";classes.mkdir(exist_ok=True);decoded=a.output/"decoded";decoded.mkdir(exist_ok=True)
def save(name,data):(models/(name+".nfm")).write_bytes(data)
for sample in ("whole","split"):
 raw=(a.samples/(sample+".nab")).read_bytes();h=struct.unpack_from("<16Q",raw)
 for owner in range(h[7]):
  packet=raw[h[8+owner*2]:h[8+owner*2]+h[9+owner*2]];start,size=struct.unpack_from("<2I",packet,36);section=packet[start:start+size];magic,count=struct.unpack_from("<2I",section)
  if magic==0x324d464e:save(sample+str(owner)+"-0",section)
  else:
   assert magic==0x314c4d4e and 2<=count<=16
   for model in range(count):start,size=struct.unpack_from("<2I",section,8+model*8);save(sample+str(owner)+"-"+str(model),section[start:start+size])
# Near-plane crossing, all-behind, and reversed-culling fixtures.
for label,points in (("near",[(-1.,-1.,.5),(-1.,1.,2.),(1.,-1.,2.)]),("behind",[(-1.,-1.,.2),(-1.,1.,.2),(1.,-1.,.2)]), ("backface",[(-1.,-1.,2.),(1.,-1.,2.),(-1.,1.,2.)])):
 data=struct.pack("<6I",0x324d464e,3,1,3,2,2)+struct.pack("<3d",120,80,100)+struct.pack("<14d",0,0,0,0,0,0,1,0,0,0,0,0,0,1)+b"".join(struct.pack("<3d",*v) for v in points)+bytes([3])+struct.pack("<3H",0,1,2)+struct.pack("<6d",0,0,0,1,1,0)+bytes([128,64,32,255])*4;save(label,data)
env=os.environ.copy();env["PATH"]=r"C:\msys64\mingw64\bin;"+env["PATH"]
def run(args):
 result=subprocess.run([str(x) for x in args],env=env,capture_output=True)
 if result.returncode:print((result.stdout+result.stderr).decode(errors="replace"));result.check_returncode()
 return result.stdout.decode()
# Cache reference inputs locally to avoid repeated compiler reads on the network.
for name in ("rigid_motion.c","rigid_motion.h","road_near_clip.h"):(a.output/name).write_bytes((work/"camera"/name).read_bytes())
(a.output/"model_mesh_reference.c").write_bytes((source/"model_mesh_reference.c").read_bytes())
run([r"C:\msys64\mingw64\bin\gcc.exe","-O2","-shared","-I"+str(a.output),a.output/"model_mesh_reference.c",a.output/"rigid_motion.c","-lm","-o",a.output/"model-reference.dll"])
run([a.jdk/"bin/javac.exe","--release","8","-d",classes,android/"java/org/codex/nfsugpreview/NativeScenePacket.java",android/"java/org/codex/nfsugpreview/NativeModelMesh.java",source/"org/codex/nfsugpreview/ModelMeshTest.java"])
text=run([a.jdk/"bin/java.exe","-cp",classes,"org.codex.nfsugpreview.ModelMeshTest",models,decoded]);print(text,flush=True)
with os.add_dll_directory(r"C:\msys64\mingw64\bin"):lib=C.CDLL(str(a.output/"model-reference.dll"))
f=lib.model_reference;f.argtypes=[C.c_void_p,C.c_size_t,C.POINTER(C.c_double),C.c_uint,C.POINTER(C.c_float),C.c_uint,C.POINTER(C.c_uint)];f.restype=C.c_int
max_camera=max_mesh=0.;cases=vertices=triangles=0
for model in sorted(models.glob("*.nfm")):
 raw=model.read_bytes();n=struct.unpack_from("<I",raw,4)[0];camera=(C.c_double*(n*3))();mesh=(C.c_float*500000)();count=C.c_uint();assert f(raw,len(raw),camera,n,mesh,100000,C.byref(count))
 jc=(decoded/(model.name+".camera")).read_bytes();jm=(decoded/(model.name+".mesh")).read_bytes();assert len(jc)==n*24 and len(jm)==count.value*20
 for i,v in enumerate(struct.unpack("<"+str(n*3)+"d",jc)):
  error=abs(v-camera[i]);assert error<=1e-9*max(1,abs(camera[i])),(model,i,v,camera[i]);max_camera=max(max_camera,error)
 for i,v in enumerate(struct.unpack("<"+str(count.value*5)+"f",jm)):
  error=abs(v-mesh[i]);assert error<=2e-6*max(1,abs(mesh[i])),(model,i,v,mesh[i]);max_mesh=max(max_mesh,error)
 h=struct.unpack_from("<6I",raw);at=160+h[1]*24+h[2]+h[3]*18;assert (decoded/(model.name+".rgba")).read_bytes()==raw[at:at+h[4]*h[5]*4]
 cases+=1;vertices+=n;triangles+=count.value//3
report=dict(result="PASS_NATIVE_MODEL_ENDPOINT_PARITY",cases=cases,source_vertices=vertices,triangles=triangles,max_camera_error=max_camera,max_mesh_float_error=max_mesh,texture_exact=True,pc_helpers=["rigid_motion.c:nf_rigid_scene_sample","road_near_clip.h:texture_near_clip"],java_stdout=text.strip(),gpu_execution=False,android_execution=False)
(a.output/"model-mesh-host-report.json").write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
