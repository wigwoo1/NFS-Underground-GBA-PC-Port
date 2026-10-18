import argparse,ctypes as C,hashlib,json,os,struct,subprocess
from pathlib import Path
p=argparse.ArgumentParser()
for name in ('output','jdk','gcc'):p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True);root=Path(__file__).resolve().parents[1];source=root.parent/'camera/road_camera_continuous.c';data=source.read_bytes();local=a.output/source.name;local.write_bytes(data);env=os.environ.copy();env['PATH']=str(a.gcc.parent)+os.pathsep+env.get('PATH','');dll=a.output/'road-camera-reference.dll'
def run(cmd):return subprocess.run(list(map(str,cmd)),check=True,capture_output=True,text=True,env=env)
run([a.gcc,'-shared','-O2',local,'-o',dll]);files=[root/'java/org/codex/nfsugpreview/NativeRoadCamera.java',root/'tests/org/codex/nfsugpreview/RoadCameraTest.java'];classes=a.output/'classes';classes.mkdir(exist_ok=True);run([a.jdk/'bin/javac.exe','--release','8','-d',classes,*files]);cases=a.output/'road-camera-cases.bin';preparation=run([a.jdk/'bin/java.exe','-cp',classes,'org.codex.nfsugpreview.RoadCameraTest',cases]).stdout.strip();os.add_dll_directory(str(a.gcc.parent));lib=C.CDLL(str(dll));fn=lib.nf_road_camera_continuous;fn.argtypes=[C.POINTER(C.c_double),C.POINTER(C.c_int32),C.POINTER(C.c_double)];fn.restype=C.c_int
payload=cases.read_bytes();magic,count=struct.unpack_from('>II',payload);assert magic==0x3143524e;at=8;accepted=rejected=0;maximum=0
for case in range(count):
 m=(C.c_int32*12)(*struct.unpack_from('>12i',payload,at));at+=48;point=(C.c_double*3)(*struct.unpack_from('>3d',payload,at));at+=24;expected=payload[at];at+=1;reference=None
 if expected:reference=struct.unpack_from('>3d',payload,at);at+=24
 before=bytes(point);mbefore=bytes(m);out=(C.c_double*3)(123456,123456,123456);good=fn(point,m,out);assert good==expected,('acceptance',case,good,expected)
 if good:
  accepted+=1
  for x,y in zip(out,reference):
   difference=abs(x-y);maximum=max(maximum,difference);assert difference<=1e-12*max(1,abs(x)),('coordinate',case,x,y)
 else:rejected+=1;assert list(out)==[123456]*3,'Non-atomic rejection'
 assert bytes(point)==before and bytes(m)==mbefore,'Input mutation'
assert at==len(payload) and source.read_bytes()==data
report={'result':'PASS_ROAD_CAMERA_C_PARITY','cases':count,'accepted':accepted,'rejected':rejected,'max_coordinate_difference':maximum,'preparation':preparation,'reference_sha256':hashlib.sha256(data).hexdigest(),'cases_sha256':hashlib.sha256(payload).hexdigest(),'source_sha256':{str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'scope':'Continuous source camera component only; original discrete source-ring projection and GPU integration remain separate'}
(a.output/'road-camera-host-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
