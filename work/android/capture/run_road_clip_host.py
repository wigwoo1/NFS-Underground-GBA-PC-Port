"""Compare complete corrected rings against canonical C, without camera substitution."""
import argparse,ctypes as C,hashlib,json,os,struct,subprocess
from pathlib import Path
p=argparse.ArgumentParser()
for name in ('output','fixtures','table','jdk','gcc'):p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args();source=Path(__file__).resolve().parent.parent;work=source.parent;java=source/'java/org/codex/nfsugpreview';a.output.mkdir(parents=True,exist_ok=True)
names=['rigid_motion.h','road_near_clip.h','road_near_attributes.h','road_source_attributes.h','road_corrected_clip.h','road_near_attributes.c'];reference_hashes={}
for name in names:
 data=(work/'camera'/name).read_bytes();(a.output/name).write_bytes(data);reference_hashes[name]=hashlib.sha256(data).hexdigest()
wrapper=a.output/'road-clip-reference.c';wrapper.write_text('#include "rigid_motion.h"\n#include "road_corrected_clip.h"\n__declspec(dllexport) int road_clip_reference(const RoadVertex*in,unsigned count,const NFRoadSourceAttributes*raw,const uint32_t*table,RoadVertex*out,unsigned*n){return texture_near_clip_corrected(in,count,out,64,raw,table,n);}\n')
env=os.environ.copy();env['PATH']=str(a.gcc.parent)+';'+env.get('PATH','')
def run(command):
 r=subprocess.run([str(x) for x in command],env=env,capture_output=True,text=True);print(r.stdout,r.stderr);r.check_returncode();return r.stdout.strip()
dll=a.output/'road-clip-reference.dll';run([a.gcc,'-shared','-O2','-I'+str(a.output),wrapper,a.output/'road_near_attributes.c','-o',dll,'-lm'])
files=[java/(n+'.java') for n in ['NativeScenePacket','NativeModelMesh','NativeWorldScene','NativeRoadAttributes','NativeRoadClip']]+[source/'tests/org/codex/nfsugpreview/RoadClipTest.java']
run([a.jdk/'bin/javac.exe','--release','8','-encoding','UTF-8','-d',a.output,*files]);preparation=run([a.jdk/'bin/java.exe','-cp',a.output,'org.codex.nfsugpreview.RoadClipTest',a.output,a.table,a.fixtures]);assert preparation.startswith('PASS_ROAD_CLIP_CASES ')
class Vertex(C.Structure):_fields_=[(n,C.c_double) for n in ('x','y','z','u','v')]
class Raw(C.Structure):_fields_=[('header',C.c_uint32*6),('offsets',C.c_int32*2),('attributes',C.c_int32*64)]
assert C.sizeof(Vertex)==40 and C.sizeof(Raw)==288
os.add_dll_directory(str(a.gcc.parent));lib=C.CDLL(str(dll));fn=lib.road_clip_reference;fn.argtypes=[C.POINTER(Vertex),C.c_uint,C.POINTER(Raw),C.POINTER(C.c_uint32),C.POINTER(Vertex),C.POINTER(C.c_uint)];fn.restype=C.c_int
table_bytes=a.table.read_bytes();normal=(C.c_uint32*32768).from_buffer_copy(table_bytes);missing=(C.c_uint32*32768).from_buffer_copy(table_bytes);missing[64]=0;tables=[normal,missing]
data=(a.output/'road-clip-cases.bin').read_bytes();magic,count=struct.unpack_from('>II',data);assert magic==0x3143504e;at=8;accepted=rejected=empty=vertices=0;max_position=max_uv=0
for case in range(count):
 flag,n=struct.unpack_from('>ii',data,at);at+=8;raw=Raw.from_buffer_copy(data[at:at+288]);at+=288;points=[]
 for i in range(n):points.append(struct.unpack_from('>3d',data,at));at+=24
 expected,written=struct.unpack_from('>ii',data,at);at+=8;ring=[]
 for i in range(written):ring.append(struct.unpack_from('>5d',data,at));at+=40
 input_points=(Vertex*n)(*(Vertex(*p,999999.5,-999999.5) for p in points));before=bytes(input_points);raw_before=bytes(raw);out=(Vertex*64)(*(Vertex(*([123456.5]*5)) for _ in range(64)));untouched=bytes(out);amount=C.c_uint(31337)
 good=fn(input_points,n,C.byref(raw),tables[flag],out,C.byref(amount));assert good==expected,('acceptance',case,good,expected)
 if good:
  accepted+=1;assert amount.value==written,('count',case,amount.value,written);vertices+=written;empty+=written==0
  for i,reference in enumerate(ring):
   actual=[getattr(out[i],name) for name in ('x','y','z','u','v')]
   for k,(x,y) in enumerate(zip(actual,reference)):
    error=abs(x-y);assert error<=1e-12*max(1,abs(x)),('ring',case,i,k,x,y)
    if k<3:max_position=max(max_position,error)
    else:max_uv=max(max_uv,error)
 else:rejected+=1;assert amount.value==31337 and bytes(out)==untouched,'Non-atomic C rejection'
 assert bytes(input_points)==before and bytes(raw)==raw_before,'C input mutation'
assert at==len(data) and bytes(normal)==table_bytes
for name,digest in reference_hashes.items():assert hashlib.sha256((work/'camera'/name).read_bytes()).hexdigest()==digest
report={'result':'PASS_CORRECTED_ROAD_RING_C_PARITY','cases':count,'accepted':accepted,'rejected':rejected,'empty_accepted':empty,'ring_vertices':vertices,'max_position_difference':max_position,'max_uv_difference':max_uv,'preparation':preparation,'reference_source_sha256':reference_hashes,'fixture_cases_sha256':hashlib.sha256(data).hexdigest(),'table_sha256':hashlib.sha256(table_bytes).hexdigest(),'source_sha256':{str(f.relative_to(source)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'scope':'Camera-space ring only; source-camera transforms, projected meshes and GPU integration remain unverified'}
(a.output/'road-clip-host-report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ('source_sha256','reference_source_sha256')},indent=2))
