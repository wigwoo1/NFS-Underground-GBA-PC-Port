from pathlib import Path
import ctypes as C,struct,subprocess,hashlib,json,os
os.environ['PATH']=r'C:\msys64\mingw64\bin;'+os.environ['PATH']
root=Path(__file__).resolve().parents[3];out=Path(r"C:\NFSUG-Workspace\NFSUG-android-sky-local");out.mkdir(exist_ok=True);camera=root/'work/camera';folder=next((camera/'prototype-runs').glob('live-sky-wrap-1791330626731057600-20'))
old=(folder/'older-sky.bin').read_bytes();new=(folder/'newer-sky.bin').read_bytes();origin=struct.unpack_from('<I',old,36)[0];rom=(root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();asset=rom[origin-0x08000000:origin-0x08000000+15376];assert len(asset)==15376;(out/'asset.bin').write_bytes(asset)
(out/'sky_phase.h').write_bytes((camera/'sky_phase.h').read_bytes());(out/'reference.c').write_text('#define NF_SKY_API __declspec(dllexport)\n#include "sky_phase.h"\n');subprocess.run([r'C:\msys64\mingw64\bin\gcc.exe','-O2','-shared',str(out/'reference.c'),'-o',str(out/'reference.dll'),'-lm'],check=True)
with os.add_dll_directory(r'C:\msys64\mingw64\bin'):d=C.CDLL(str(out/'reference.dll'))
class Boundary(C.Structure):_fields_=[('epoch',C.c_uint64),('refresh',C.c_uint32),('angle',C.c_uint32),('source',C.c_uint32),('origin',C.c_uint32),('destination',C.c_uint32),('center',C.c_int32),('indices',C.c_void_p)]
class Sample(C.Structure):_fields_=[('lower',C.c_void_p),('upper',C.c_void_p),('phase',C.c_double),('weight',C.c_double),('lower_offset',C.c_uint),('upper_offset',C.c_uint),('exact',C.c_uint)]
d.nf_sky_boundary_decode.argtypes=[C.c_void_p,C.c_size_t,C.POINTER(Boundary)];d.nf_sky_phase_sample.argtypes=[C.POINTER(Boundary),C.POINTER(Boundary),C.c_void_p,C.c_size_t,C.c_double,C.c_uint,C.POINTER(Sample)]
pairs=[(old,new)]
for angles in ((4090,4104),(4104,4090),(16380,8),(8,16380)):
 pair=[]
 for i,angle in enumerate(angles):
  h=list(struct.unpack_from('<14I',old));h[4]=100+i;h[5]=angle;h[8]=origin+((((angle&16383)*240)>>12)%240&~1);h[12]=0;offset=h[8]-origin;pair.append(struct.pack('<14I',*h)+asset[offset:offset+15136])
 pairs.append(pair)
lines=[]
for index,(a,b) in enumerate(pairs):
 (out/f'pair-{index}-old.bin').write_bytes(a);(out/f'pair-{index}-new.bin').write_bytes(b);ab=C.create_string_buffer(a);bb=C.create_string_buffer(b);aa=Boundary();ba=Boundary();assert d.nf_sky_boundary_decode(ab,len(a),C.byref(aa)) and d.nf_sky_boundary_decode(bb,len(b),C.byref(ba))
 for mode in (0,1):
  for k in range(33):
   alpha=k/32;s=Sample();assert d.nf_sky_phase_sample(C.byref(aa),C.byref(ba),asset,len(asset),alpha,mode,C.byref(s))
   values=[index,mode,alpha,s.phase,s.weight,s.lower_offset,s.upper_offset,s.exact,hashlib.sha256(C.string_at(s.lower,15136)).hexdigest(),hashlib.sha256(C.string_at(s.upper,15136)).hexdigest()];lines.append('\t'.join(map(str,values)))
(out/'samples.tsv').write_text('\n'.join(lines));jdk=Path(r'C:\NFSUG-Workspace\android-tools\jdk-21.0.12.1+1');classes=out/'classes';classes.mkdir(exist_ok=True);files=[root/'work/android/java/org/codex/nfsugpreview/NativeSky.java',root/'work/android/tests/org/codex/nfsugpreview/SkyTest.java'];subprocess.run([str(jdk/'bin/javac.exe'),'--release','8','-d',str(classes),*map(str,files)],check=True);run=subprocess.run([str(jdk/'bin/java.exe'),'-cp',str(classes),'org.codex.nfsugpreview.SkyTest',str(out)],check=True,capture_output=True,text=True);print(run.stdout);report=dict(result='PASS_SKY_JAVA_C_PARITY',samples=len(lines),real_pairs=1,synthetic_wrap_pairs=4,java_stdout=run.stdout.strip(),source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files},gpu=False,android_runtime=False);(out/'sky-host-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
