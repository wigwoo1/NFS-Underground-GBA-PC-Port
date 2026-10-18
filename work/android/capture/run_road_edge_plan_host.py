from pathlib import Path
import ctypes as C,os,struct,json,hashlib,subprocess
root=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');out=Path(r'C:\NFSUG-Workspace\NFSUG-android-source-road-assets-local');table=(root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()[0x627700:0x647700]
with os.add_dll_directory(r'C:\msys64\mingw64\bin'):lib=C.CDLL(r'C:\NFSUG-Workspace\NFSUG-android-source-background-local\road-perspective-reference.dll')
u=C.c_uint32;f=lib.nf_road_perspective_plan;f.argtypes=[C.POINTER(u),C.POINTER(u),C.POINTER(u),C.c_uint,C.POINTER(C.c_uint),C.POINTER(u)];rec=(u*32768).from_buffer_copy(table);manifest=json.loads((out/'source-fixture-capture-report.json').read_text());assets=[a for r in manifest['road_records'] for a in r['assets']];parts=[table,struct.pack('<I',len(assets))];total=0
for a in assets:
 raw=(out/a['filename']).read_bytes();assert hashlib.sha256(raw).hexdigest()==a['sha256'];h=struct.unpack_from('<10I',raw);records=[]
 for i in range(h[5]):
  s=struct.unpack_from('<20I',raw,40+i*80);p=s[4:]
  if s[2]==0x03003190:
   output=(u*512)();final=(u*16)();n=C.c_uint();assert f((u*16)(*p),rec,output,32,C.byref(n),final);runs=[list(output)[j*16:j*16+16] for j in range(n.value)]
  else:runs=[p]
  at=0;base=0x0600a000 if s[0]>=0x0600a000 else 0x06000000
  for c in runs:
   uv,vv=c[8:10]
   for k in range(c[7]):
    uv&=c[1];vv&=c[2];tex=2*((uv>>16)+((vv>>16)<<c[0]))
    for duplicate in range(s[3]+1):
     for lane in range(2):
      dest=s[0]-base+at*2+duplicate*240+lane;y,x=divmod(dest,240)
      if y>=160 or x<238:continue
      assert tex+lane<h[8];records.append((x,y,tex+lane))
    uv=(uv+c[10])&0xffffffff;vv=(vv+c[11])&0xffffffff;at+=1
  assert at==s[1]
 name=a['filename'].encode();parts.extend((struct.pack('<I',len(name)),name,struct.pack('<I',len(records)),b''.join(struct.pack('<3I',*r) for r in records)));total+=len(records)
(out/'edge-reference.bin').write_bytes(b''.join(parts));jdk=Path(r'C:\NFSUG-Workspace\android-tools\jdk-21.0.12.1+1');java=root/'work/android/java/org/codex/nfsugpreview';files=[java/(n+'.java') for n in ('NativeRoadAsset','NativeRoadPerspective','NativeRoadEdgePlan')]+[root/'work/android/tests/org/codex/nfsugpreview/RoadEdgePlanTest.java'];classes=out/'edge-classes';classes.mkdir(exist_ok=True);subprocess.run([str(jdk/'bin/javac.exe'),'--release','8','-d',str(classes),*map(str,files)],check=True);r=subprocess.run([str(jdk/'bin/java.exe'),'-cp',str(classes),'org.codex.nfsugpreview.RoadEdgePlanTest',str(out)],check=True,capture_output=True,text=True);print(r.stdout);(out/'edge-plan-report.json').write_text(json.dumps(dict(result=r.stdout.strip(),assets=len(assets),ordered_writes=total,gpu=False,reference='C perspective plan plus independent Python address enumeration'),indent=2))
