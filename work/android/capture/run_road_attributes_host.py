"""Compare Java source UV correction directly with canonical native C functions."""
import argparse,ctypes as C,hashlib,json,os,struct,subprocess
from pathlib import Path
p=argparse.ArgumentParser()
for name in ('output','fixtures','sample','jdk','gcc'):p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args();source=Path(__file__).resolve().parent.parent;project=source.parents[1];java=source/'java/org/codex/nfsugpreview';a.output.mkdir(parents=True,exist_ok=True)
original=project/'work/camera/road_near_attributes.c';data=original.read_bytes();reference=a.output/'road_near_attributes.reference.c';reference.write_bytes(data);dll=a.output/'road-attributes-reference.dll'
env=os.environ.copy();env['PATH']=str(a.gcc.parent)+';'+env.get('PATH','')
def run(command):
 r=subprocess.run([str(x) for x in command],env=env,capture_output=True,text=True);print(r.stdout,r.stderr);r.check_returncode();return r.stdout.strip()
run([a.gcc,'-shared','-O2',reference,'-o',dll,'-lm'])
names=['NativeScenePacket','NativeSceneSnapshot','NativeModelMesh','NativeWorldScene','NativeRoadAttributes'];files=[java/(n+'.java') for n in names]+[source/'tests/org/codex/nfsugpreview/RoadAttributesTest.java']
run([a.jdk/'bin/javac.exe','--release','8','-encoding','UTF-8','-d',a.output,*files]);preparation=run([a.jdk/'bin/java.exe','-cp',a.output,'org.codex.nfsugpreview.RoadAttributesTest',a.output,a.sample,a.fixtures]);assert preparation.startswith('PASS_ROAD_ATTRIBUTE_CASES ')
os.add_dll_directory(str(a.gcc.parent));library=C.CDLL(str(dll));vertex=library.nf_road_vertex_attributes;near=library.nf_road_near_attributes;table_bytes=(a.output/'reciprocal.bin').read_bytes();table=(C.c_uint32*32768).from_buffer_copy(table_bytes)
vertex.argtypes=[C.c_double,C.POINTER(C.c_int32),C.c_uint,C.c_uint,C.c_uint,C.POINTER(C.c_uint32),C.POINTER(C.c_double)];near.argtypes=[C.c_double,C.c_double,C.POINTER(C.c_int32),C.c_uint,C.c_uint,C.c_uint,C.c_int,C.POINTER(C.c_uint32),C.POINTER(C.c_double)]
raw=(a.output/'road-attribute-cases.bin').read_bytes();magic,count=struct.unpack_from('>II',raw);record=struct.Struct('>5i2d5i2d');assert magic==0x3141524e and len(raw)==8+count*record.size
accepted=rejected=0;maximum=0
for case in range(count):
 kind,shift,height,affine,cut,z0,z1,a0,a1,a2,a3,expected,u,v=record.unpack_from(raw,8+case*record.size);attributes=(C.c_int32*4)(a0,a1,a2,a3);out=(C.c_double*2)(123456.5,123456.5)
 good=vertex(z0,attributes,shift,height,affine,table,out) if kind==0 else near(z0,z1,attributes,shift,height,affine,cut,table,out)
 assert good==expected,('acceptance',case,good,expected)
 if good:
  accepted+=1
  for actual,wanted in zip(out,(u,v)):
   error=abs(actual-wanted);maximum=max(maximum,error);assert error<=1e-12*max(1,abs(actual)),('UV mismatch',case,actual,wanted)
 else:rejected+=1;assert tuple(out)==(123456.5,123456.5),'Non-atomic C rejection'
 assert tuple(attributes)==(a0,a1,a2,a3),'C input attributes mutated'
assert bytes(table)==table_bytes and hashlib.sha256(original.read_bytes()).digest()==hashlib.sha256(data).digest()
report={'result':'PASS_ROAD_SOURCE_ATTRIBUTE_C_PARITY','cases':count,'accepted':accepted,'rejected':rejected,'max_uv_difference':maximum,'preparation':preparation,'reference_source_sha256':hashlib.sha256(data).hexdigest(),'reference_dll_sha256':hashlib.sha256(dll.read_bytes()).hexdigest(),'fixture_cases_sha256':hashlib.sha256(raw).hexdigest(),'table_sha256':hashlib.sha256(table_bytes).hexdigest(),'source_sha256':{str(f.relative_to(source)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'gpu_corrected_clipping_verified':False}
(a.output/'road-attributes-host-report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'},indent=2))
