from pathlib import Path
import ctypes as C,struct,random,subprocess,os,json,hashlib
root=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');out=Path(r'C:\NFSUG-Workspace\NFSUG-android-source-background-local');src=root/'work/camera/road_polygon_clip.c';dll=out/'road-perspective-reference.dll'
env=os.environ.copy();env['PATH']=r'C:\msys64\mingw64\bin;'+env['PATH'];subprocess.run([r'C:\msys64\mingw64\bin\gcc.exe','-shared','-O2',str(src),'-o',str(dll)],env=env,check=True)
with os.add_dll_directory(r'C:\msys64\mingw64\bin'): lib=C.CDLL(str(dll))
u=C.c_uint32;f=lib.nf_road_perspective_plan;f.argtypes=[C.POINTER(u),C.POINTER(u),C.POINTER(u),C.c_uint,C.POINTER(C.c_uint),C.POINTER(u)];f.restype=C.c_int
rom=(root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=rom[0x627700:0x647700];rec=(u*32768).from_buffer_copy(table);rng=random.Random(3190);cases=[]
for i in range(1200):
 p=[rng.getrandbits(32) for _ in range(16)];p[7]=[0,1,15,16,17,121,512,513][i%8];p[10]=rng.randrange(16,500000);p[13]=(p[10]+rng.randrange(-1000,1001))&0xffffffff;p[4]=rng.choice([0,1,16,256,4096,0xffffffff,0x7fffffff]);cap=rng.choice([0,1,8,32]);a=(u*16)(*p);result=(u*512)();final=(u*16)();n=C.c_uint();ok=f(a,rec,result,cap,C.byref(n),final);entry=struct.pack('<16I3I',*p,cap,ok,n.value if ok else 0)
 if ok:entry+=bytes(result)[:n.value*64]+bytes(final)
 cases.append(entry)
real_count=0
assets=Path(r'C:\NFSUG-Workspace\NFSUG-android-source-road-assets-local');capture=json.loads((assets/'source-fixture-capture-report.json').read_text())
for owner in capture['road_records']:
 for record in owner['assets']:
  raw=(assets/record['filename']).read_bytes();assert hashlib.sha256(raw).hexdigest()==record['sha256'];header=struct.unpack_from('<10I',raw)
  for i in range(header[5]):
   span=struct.unpack_from('<20I',raw,40+i*80)
   if span[2]!=0x03003190:continue
   p=span[4:];a=(u*16)(*p);result=(u*512)();final=(u*16)();n=C.c_uint();ok=f(a,rec,result,32,C.byref(n),final);assert ok
   cases.append(struct.pack('<16I3I',*p,32,ok,n.value)+bytes(result)[:n.value*64]+bytes(final));real_count+=1
assert real_count>0
fixture=out/'road-perspective-c-reference.bin';fixture.write_bytes(table+struct.pack('<I',len(cases))+b''.join(cases));java=root/'work/android/java/org/codex/nfsugpreview/NativeRoadPerspective.java';test=root/'work/android/tests/org/codex/nfsugpreview/RoadPerspectiveTest.java';jdk=Path(r'C:\NFSUG-Workspace\android-tools\jdk-21.0.12.1+1');classes=out/'background-classes';subprocess.run([str(jdk/'bin/javac.exe'),'--release','8','-d',str(classes),str(java),str(test)],check=True);r=subprocess.run([str(jdk/'bin/java.exe'),'-cp',str(classes),'org.codex.nfsugpreview.RoadPerspectiveTest',str(fixture)],check=True,capture_output=True,text=True);print(r.stdout);(out/'road-perspective-report.json').write_text(json.dumps(dict(result=r.stdout.strip(),c_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),java_sha256=hashlib.sha256(java.read_bytes()).hexdigest(),fixture_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),real_spans=real_count),indent=2))
