"""Parity-check Java world/material/order decoding against native scene_packet.c."""
from pathlib import Path
import argparse,ctypes as C,hashlib,json,os,struct,subprocess,collections
p=argparse.ArgumentParser()
for n in ("output","samples","jdk","native_source"):p.add_argument("--"+n.replace("_","-"),type=Path,required=True)
a=p.parse_args();source=Path(__file__).resolve().parent;android=source.parent;a.output.mkdir(parents=True,exist_ok=True);fixtures=a.output/"fixtures";fixtures.mkdir(exist_ok=True);decoded=a.output/"decoded";decoded.mkdir(exist_ok=True)
u=lambda b,o=0:struct.unpack_from("<I",b,o)[0]
def sections(raw):return [raw[u(raw,36+i*12):u(raw,36+i*12)+u(raw,40+i*12)] for i in range(5)]
def build(parts):
 out=bytearray(96);struct.pack_into("<8I",out,0,0x3150534e,1,len(out),5,1,10,11,0)
 for i,b in enumerate(parts):
  out+=bytes((-len(out))%8);start=len(out);out+=b;struct.pack_into("<3I",out,32+i*12,i+1,start,len(b))
 struct.pack_into("<I",out,8,len(out));return bytes(out)
actual=[]
for label in ("whole","split"):
 b=(a.samples/(label+".nab")).read_bytes();h=struct.unpack_from("<16Q",b)
 for owner in range(h[7]):
  raw=b[h[8+owner*2]:h[8+owner*2]+h[9+owner*2]];name=label+str(owner);(fixtures/(name+".nsp")).write_bytes(raw);actual.append(raw)
models=sections(actual[0])[0]
if u(models)==0x314c4d4e:at,n=struct.unpack_from("<2I",models,8);model=models[at:at+n]
else:model=models
valid={};bounds=struct.pack("<2Id4H",0x3142464e,1,.5,0,240,0,160)
for mode in range(11):
 count,w,h=4,4,2;pixels=w*h;states=bytes([0,2,2,0,2,2,2,0]);planes=17 if mode in (3,8) else 1
 stateplanes=b"".join(bytes(0 if s==0 else 1 if level and (i+level)%2 else 2 for i,s in enumerate(states)) for level in range(planes))
 attrs=[(0,0),(16384,0),(16384,16384),(0,16384)]+[(0,0)]*28
 rawattrs=struct.pack("<6I2i",count,2,h*2,int(mode in (6,10)),0x2000,0x3000,0,0)+b"".join(struct.pack("<2i",*v) for v in attrs)
 payload=bytes(range(pixels))
 if mode==0:payload=b""
 elif mode in (2,3):payload=stateplanes
 elif mode in (7,8):payload=stateplanes+bytes((i%254)+1 if s==2 else 0 for i,s in enumerate(stateplanes))
 elif mode in (5,6):payload+=rawattrs
 elif mode in (9,10):payload+=struct.pack("<14I",1,0x3000000,16384,0,0,0,16384,0,0,0,16384,0,0,0)+rawattrs
 xyz=struct.pack("<12d",-1,0,10,1,0,10,1,0,20,-1,0,20);uv=struct.pack("<8d",0,0,1,0,1,1,0,1)
 surface=struct.pack("<3I",count,w,h)+xyz+uv+bytes([50,80,100,255])*pixels
 world=struct.pack("<2I",0x31444652,1)+surface+struct.pack("<4I",0x3149574e,1,mode,len(payload))+payload
 lit=mode in (3,8);lighting=struct.pack("<3I",0x314c464e,1,int(lit))+(struct.pack("<4I",0,0,w,h)+bytes((i%256 for i in range(pixels*64))) if lit else b"")+bytes(32768*4)
 identity=struct.pack("<2I10I",0x3149464e,2,2 if mode in (2,3,7,8) else 1,1,2,3,0,3,1,2,3,0)+bounds
 parts=[model,world,struct.pack("<4I",0x314f464e,2,0,0xffffffff),lighting,identity];valid[mode]=parts;(fixtures/("mode"+str(mode)+".nsp")).write_bytes(build(parts))
bad=0
def mutate(mode,section,offset,data):
 global bad
 parts=list(valid[mode]);v=bytearray(parts[section]);v[offset:offset+len(data)]=data;parts[section]=bytes(v);(fixtures/("bad-"+str(bad)+".nsp")).write_bytes(build(parts));bad+=1
for offset,value in ((0,0),(4,129),(8,2),(12,0)):mutate(0,1,offset,struct.pack("<I",value))
mutate(0,1,20,struct.pack("<d",float("nan")))
base=8+12+4*40+4*2*4
mutate(0,1,base+8,struct.pack("<I",11));mutate(1,1,base+12,struct.pack("<I",1))
mutate(7,1,base+16+1,bytes([3]));mutate(7,1,base+16+8+1,bytes([0]))
mutate(5,1,base+16+8+4,struct.pack("<I",3));mutate(5,1,base+16+8+32+4*8,struct.pack("<i",1));mutate(5,1,8+12+4*24,struct.pack("<d",.125))
mutate(0,2,12,struct.pack("<I",0));mutate(0,2,12,struct.pack("<I",0xfffffffe));mutate(1,4,8,struct.pack("<I",2));mutate(8,3,20,struct.pack("<I",5));mutate(0,4,8+40+16,struct.pack("<H",241))
env=os.environ.copy();env["PATH"]=r"C:\msys64\mingw64\bin;"+env["PATH"]
def run(args):
 r=subprocess.run([str(x) for x in args],env=env,capture_output=True)
 if r.returncode:print((r.stdout+r.stderr).decode(errors="replace"));r.check_returncode()
 return r.stdout.decode()
# The C reference includes its real snapshot-store/timeline dependency closure.
for name in ("scene_packet.c","snapshot_store.c","presentation_timeline.c"):
 assert (a.native_source/name).read_bytes()==(android.parent/"camera"/name).read_bytes(),"Stale canonical reference: "+name
(a.output/"world_decode_reference.c").write_bytes((source/"world_decode_reference.c").read_bytes())
run([r"C:\msys64\mingw64\bin\gcc.exe","-O2","-shared","-ffunction-sections","-fdata-sections","-I"+str(a.native_source),a.output/"world_decode_reference.c","-Wl,--gc-sections","-lm","-o",a.output/"world-reference.dll"])
classes=a.output/"classes";classes.mkdir(exist_ok=True)
run([a.jdk/"bin/javac.exe","--release","8","-d",classes]+[android/"java/org/codex/nfsugpreview"/(n+".java") for n in ("NativeScenePacket","NativeModelMesh","NativeWorldScene")]+[source/"org/codex/nfsugpreview/WorldDecodeTest.java"])
text=run([a.jdk/"bin/java.exe","-cp",classes,"org.codex.nfsugpreview.WorldDecodeTest",fixtures,decoded]);print(text,flush=True)
with os.add_dll_directory(r"C:\msys64\mingw64\bin"):d=C.CDLL(str(a.output/"world-reference.dll"))
f=d.world_reference;f.argtypes=[C.c_void_p,C.c_size_t,C.POINTER(C.c_uint32),C.c_uint];f.restype=C.c_int
sha=lambda b:hashlib.sha256(b).hexdigest();surface_count=0;hist=collections.Counter();cases=0
for file in sorted(fixtures.glob("*.nsp")):
 raw=file.read_bytes();out=(C.c_uint32*1028)();accepted=f(raw,len(raw),out,1028)
 if file.name.startswith("bad-"):assert not accepted,file;continue
 assert accepted,file;parts=sections(raw);lines=(decoded/(file.name+".txt")).read_text().splitlines();assert list(map(int,lines[0].split()))==list(out[:3]);world=parts[1];at=8;items=[]
 for i in range(out[0]):n,w,h=struct.unpack_from("<3I",world,at);size=12+n*40+w*h*4;items.append((world[at:at+size],b""));at+=size
 if at<len(world):
  at+=8
  for i in range(out[0]):mode,size=struct.unpack_from("<2I",world,at);at+=8;items[i]=(items[i][0],world[at:at+size]);at+=size
 light=8
 for i,(surface,meta) in enumerate(items):
  line=lines[1+i].split();n,w,h,size,mode,meta_size,kind,enabled=list(out[4+i*8:12+i*8]);assert list(map(int,line[:7]))==[i,kind,mode,n,w,h,enabled]
  light_size=4+(16+w*h*64 if enabled else 0);expected=[sha(surface[12:12+n*24]),sha(surface[12+n*24:12+n*40]),sha(surface[12+n*40:]),sha(meta),sha(parts[3][light:light+light_size])];assert line[7:]==expected,(file,i);light+=light_size;hist[mode]+=1;surface_count+=1
 order=struct.unpack_from('<'+str(out[2])+'I',parts[2],8);expected_order=[('M'+str(0xffffffff-v)) if v>=0xfffffff0 else 'W'+str(v) for v in order];assert lines[1+out[0]].split()==expected_order
 idbase=8+(out[0]+out[1])*20;assert lines[2+out[0]].split()==[sha(parts[3][light:]),sha(parts[4][idbase:])];cases+=1
report=dict(result="PASS_WORLD_MATERIAL_ORDER_PARITY",valid_packets=cases,malformed_packets=bad,surfaces=surface_count,material_mode_histogram=dict(hist),all_surface_bytes_exact=True,all_commands_exact=True,lighting_and_bounds_exact=True,c_reference='scene_packet.c:nf_scene_packet_view/nf_scene_world_metadata_all',java_stdout=text.strip(),gpu_execution=False,android_execution=False)
(a.output/"world-decode-report.json").write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
