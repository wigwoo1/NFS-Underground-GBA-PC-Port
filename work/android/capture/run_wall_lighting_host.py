"""Compare native Java shade columns with the canonical PC C helper."""
import argparse,ctypes as C,hashlib,json,os,struct,subprocess,uuid
from pathlib import Path
p=argparse.ArgumentParser()
for name in ('output','fixtures','jdk','gcc'):p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args();source=Path(__file__).resolve().parent.parent;project=source.parents[1];java=source/'java/org/codex/nfsugpreview';a.output.mkdir(parents=True,exist_ok=True)
header=project/'work/camera/narrow_wall_shading.h';data=header.read_bytes();(a.output/header.name).write_bytes(data)
wrapper=a.output/'wall-light-reference.c';wrapper.write_text('#include "narrow_wall_shading.h"\n__declspec(dllexport) int wall_light_reference(const double*x,const double*z,const double*s,int*out,unsigned n){return nf_narrow_wall_shades(x,z,s,out,n);}\n')
env=os.environ.copy();env['PATH']=str(a.gcc.parent)+';'+env.get('PATH','')
def run(command):
 r=subprocess.run([str(x) for x in command],env=env,capture_output=True,text=True);print(r.stdout,r.stderr);r.check_returncode();return r.stdout.strip()
dll=a.output/'wall-light-reference.dll';run([a.gcc,'-shared','-O2',wrapper,'-o',dll,'-lm'])
names=['NativeScenePacket','NativeSceneSnapshot','NativeModelMesh','NativeWorldScene','NativeWorldMesh','NativeRoadCamera','NativeRoadProjection','NativeRoadAttributes','NativeRoadClip','NativeWallLighting'];files=[java/(n+'.java') for n in names]+[source/'tests/org/codex/nfsugpreview/WallLightingTest.java']
run([a.jdk/'bin/javac.exe','--release','8','-encoding','UTF-8','-d',a.output,*files]);cases=a.output/('cases-'+uuid.uuid4().hex[:8]);preparation=run([a.jdk/'bin/java.exe','-cp',a.output,'org.codex.nfsugpreview.WallLightingTest',cases,a.fixtures]);assert preparation.startswith('PASS_WALL_LIGHT_PREPARATION ')
os.add_dll_directory(str(a.gcc.parent));library=C.CDLL(str(dll));fn=library.wall_light_reference;fn.argtypes=[C.POINTER(C.c_double)]*3+[C.POINTER(C.c_int),C.c_uint];fn.restype=C.c_int
case_count=columns=0;levels=set()
for case in sorted(cases.glob('*.case')):
 raw=case.read_bytes();count,*values=struct.unpack_from('>i6d',raw);expected=struct.unpack_from('>'+str(count)+'i',raw,52);assert len(raw)==52+count*4;out=(C.c_int*count)();assert fn((C.c_double*2)(*values[:2]),(C.c_double*2)(*values[2:4]),(C.c_double*2)(*values[4:6]),out,count)==1;assert tuple(out)==expected,'C shade mismatch: '+str(case);levels.update(expected);columns+=count;case_count+=1
assert case_count>0 and columns>0 and hashlib.sha256(header.read_bytes()).digest()==hashlib.sha256(data).digest()
report={'result':'PASS_NATIVE_WALL_LIGHT_C_PARITY','cases':case_count,'exact_shade_columns':columns,'levels_seen':sorted(levels),'preparation':preparation,'reference_header_sha256':hashlib.sha256(data).hexdigest(),'reference_dll_sha256':hashlib.sha256(dll.read_bytes()).hexdigest(),'source_sha256':{str(f.relative_to(source)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'scope':'PC native perspective wall shade rule; not bit-exact GBA quantized columns or lit GPU materials','gpu_lighting_verified':False}
(a.output/'wall-lighting-host-report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'},indent=2))
