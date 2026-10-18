"""Check endpoint world meshes against canonical PC camera/clip/ear helpers."""
from pathlib import Path
import argparse,ctypes as C,json,os,struct,subprocess
p=argparse.ArgumentParser()
for n in ("output","world_data","jdk"):p.add_argument("--"+n.replace("_","-"),type=Path,required=True)
a=p.parse_args();source=Path(__file__).resolve().parent;android=source.parent;work=android.parent;a.output.mkdir(parents=True,exist_ok=True);decoded=a.output/"decoded";decoded.mkdir(exist_ok=True);fixtures=a.world_data/"fixtures"
u=lambda b,o=0:struct.unpack_from("<I",b,o)[0]
def sections(raw):return [raw[u(raw,36+i*12):u(raw,36+i*12)+u(raw,40+i*12)] for i in range(5)]
def build(parts):
 out=bytearray(96);struct.pack_into("<8I",out,0,0x3150534e,1,0,5,1,10,11,0)
 for i,b in enumerate(parts):out+=bytes((-len(out))%8);start=len(out);out+=b;struct.pack_into("<3I",out,32+i*12,i+1,start,len(b))
 struct.pack_into("<I",out,8,len(out));return bytes(out)
for mode in (0,4):
 parts=sections((fixtures/"mode0.nsp").read_bytes());model=bytearray(parts[0]);struct.pack_into("<3d",model,24,120,80,100);struct.pack_into("<7d",model,48,0,0,0,0,0,0,1);parts[0]=bytes(model)
 points=[(-30,-10,32),(30,-10,100),(5,0,100),(30,30,100),(-30,30,100)];uv=[(0,0),(1,0),(.5,.5),(1,1),(0,1)];payload=bytes(range(8)) if mode else b""
 parts[1]=struct.pack("<5I",0x31444652,1,5,4,2)+b"".join(struct.pack("<3d",*v) for v in points)+b"".join(struct.pack("<2d",*v) for v in uv)+bytes([50,80,100,255])*8+struct.pack("<4I",0x3149574e,1,mode,len(payload))+payload
 (fixtures/("near-concave-"+str(mode)+".nsp")).write_bytes(build(parts))
env=os.environ.copy();env["PATH"]=r"C:\msys64\mingw64\bin;"+env["PATH"]
def run(args):
 r=subprocess.run([str(x) for x in args],env=env,capture_output=True)
 if r.returncode:print((r.stdout+r.stderr).decode(errors="replace"));r.check_returncode()
 return r.stdout.decode()
for name in ("rigid_motion.c","rigid_motion.h","road_near_clip.h","road_triangulate.h"):(a.output/name).write_bytes((work/"camera"/name).read_bytes())
(a.output/"world_mesh_reference.c").write_bytes((source/"world_mesh_reference.c").read_bytes())
run([r"C:\msys64\mingw64\bin\gcc.exe","-O2","-shared","-I"+str(a.output),a.output/"world_mesh_reference.c",a.output/"rigid_motion.c","-lm","-o",a.output/"world-mesh-reference.dll"])
classes=a.output/"classes";classes.mkdir(exist_ok=True)
run([a.jdk/"bin/javac.exe","--release","8","-d",classes]+[android/"java/org/codex/nfsugpreview"/(n+".java") for n in ("NativeScenePacket","NativeModelMesh","NativeWorldScene","NativeWorldMesh","NativeRoadCamera","NativeRoadProjection","NativeRoadAttributes","NativeRoadClip")]+[source/"org/codex/nfsugpreview/WorldMeshTest.java"])
text=run([a.jdk/"bin/java.exe","-cp",classes,"org.codex.nfsugpreview.WorldMeshTest",fixtures,decoded]);print(text,flush=True)
with os.add_dll_directory(r"C:\msys64\mingw64\bin"):lib=C.CDLL(str(a.output/"world-mesh-reference.dll"));validator=C.CDLL(str(a.world_data/"world-reference.dll"))
f=lib.world_mesh_reference;f.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_uint,C.POINTER(C.c_double),C.POINTER(C.c_float),C.c_uint,C.POINTER(C.c_uint)];f.restype=C.c_int
v=validator.world_reference;v.argtypes=[C.c_void_p,C.c_size_t,C.POINTER(C.c_uint32),C.c_uint];v.restype=C.c_int
cases=triangles=rejected=0;max_camera=max_mesh=0.
for file in sorted(fixtures.glob("*.nsp")):
 if file.name.startswith("bad-"):continue
 raw=file.read_bytes();summary=(C.c_uint32*1028)();assert v(raw,len(raw),summary,1028),file;parts=sections(raw);model=parts[0]
 if u(model)==0x314c4d4e:start,size=struct.unpack_from("<2I",model,8);model=model[start:start+size]
 world=parts[1];at=8
 for i in range(summary[0]):
  n,w,h=struct.unpack_from("<3I",world,at);size=12+n*40+w*h*4;surface=world[at:at+size];at+=size;mode=summary[4+i*8+4]
  if mode in (5,6,9,10):rejected+=1;continue
  camera=(C.c_double*(n*3))();mesh=(C.c_float*960)();count=C.c_uint();assert f(model,len(model),surface,len(surface),int(mode==4),camera,mesh,192,C.byref(count))
  prefix=file.name+"-"+str(i);jc=(decoded/(prefix+".camera")).read_bytes();jm=(decoded/(prefix+".mesh")).read_bytes();assert len(jc)==n*24 and len(jm)==count.value*20,(file,i)
  for j,x in enumerate(struct.unpack('<'+str(n*3)+'d',jc)):
   error=abs(x-camera[j]);assert error<=1e-9*max(1,abs(camera[j])),(file,i,j);max_camera=max(max_camera,error)
  for j,x in enumerate(struct.unpack('<'+str(count.value*5)+'f',jm)):
   error=abs(x-mesh[j]);assert error<=2e-6*max(1,abs(mesh[j])),(file,i,j,x,mesh[j]);max_mesh=max(max_mesh,error)
  cases+=1;triangles+=count.value//3
report=dict(result="PASS_NATIVE_WORLD_ENDPOINT_MESH_PARITY",meshes=cases,triangles=triangles,source_corrected_modes_excluded_from_legacy_reference=rejected,max_camera_error=max_camera,max_float_error=max_mesh,near_concave_perspective_and_affine=True,c_helpers=["nf_rigid_scene_sample","texture_near_clip","road_triangulate"],java_stdout=text.strip(),gpu_execution=False,android_execution=False)
(a.output/"world-mesh-report.json").write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
