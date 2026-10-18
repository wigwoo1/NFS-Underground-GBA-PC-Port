"""Compare Android's model-only compatibility plane against the proven PC helper.
Host Java component proof; not Android GLES or gameplay proof.
"""
from pathlib import Path
import ctypes as C,hashlib,json,os,shutil,struct,subprocess
source=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-Android-Empty-Model-Plane-20261017';pc=source.parent/'pc';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
tool=json.loads((base/'android-tools/android-app-toolchain.json').read_text());jdk=Path(tool['jdk']);inputs=[];frozen=[]
for path in [base/'NFSUG-pc-scene-prepare-failure-replay/failing-model-vertices.bin',base/'NFSUG-pc-empty-plane-second-failure/model-vertices.bin']:
 raw=path.read_bytes();assert len(raw)%60==0;inputs.extend(struct.unpack_from('<15f',raw,i) for i in range(0,len(raw),60));frozen.append(dict(path=str(path),sha256=sha(path),triangles=len(raw)//60))
v=[50,87,0,0,1,100,87,1,0,1,150,87,1,1,1]
for xy in [[50,87,100,87,150,87],[100,40,100,80,100,120],[100,87]*3,[50,40,150,120,50,40],[50,40,50,40,150,120],[50,40,150,120,150,120],[50,87.25,150,87.25,100,87.75],[50,40,150,40,100,120],[0,0,1,1,2,2]]:
 row=v.copy()
 for i in range(3):row[i*5:i*5+2]=xy[i*2:i*2+2]
 inputs.append(row)
for i in range(15):
 for value in [float('nan'),float('inf'),float('-inf')]:
  row=v.copy();row[i]=value;inputs.append(row)
for i in [4,9,14]:
 for value in [0,-1]:row=v.copy();row[i]=value;inputs.append(row)
row=v.copy();row[2]=3e38;row[4]=1e-40;inputs.append(row)
raw=b''.join(struct.pack('<15f',*v) for v in inputs);(out/'triangles.bin').write_bytes(raw);inputs=[struct.unpack_from('<15f',raw,i) for i in range(0,len(raw),60)]
runner=r"""package org.codex.nfsugpreview;
import java.nio.*;import java.nio.file.*;import java.io.*;import java.lang.reflect.*;
public final class EmptyPlaneHostTest {
 static void write(ByteBuffer out,FloatBuffer v,boolean model)throws Exception{
  int position=v.position(),limit=v.limit();
  NativeTexturePlane p=null;
  try{p=model?NativeTexturePlane.class.getDeclaredConstructor(FloatBuffer.class,int.class,boolean.class).newInstance(v,0,true):new NativeTexturePlane(v,0);}
  catch(InvocationTargetException failure){if(!(failure.getCause() instanceof IllegalArgumentException))throw failure;}
  catch(IllegalArgumentException expected){}
  if(v.position()!=position||v.limit()!=limit)throw new AssertionError("Input buffer mutated");
  out.putInt(p==null?0:1);
  if(p==null){for(int i=0;i<11;i++)out.putFloat(0);return;}
  out.putFloat(p.x).putFloat(p.y);for(float f:p.base)out.putFloat(f);for(float f:p.dx)out.putFloat(f);for(float f:p.dy)out.putFloat(f);
 }
 public static void main(String[] args)throws Exception{
  byte[] data=Files.readAllBytes(Paths.get(args[0]));ByteBuffer in=ByteBuffer.wrap(data).order(ByteOrder.LITTLE_ENDIAN),out=ByteBuffer.allocate(data.length/60*96).order(ByteOrder.LITTLE_ENDIAN);
  while(in.hasRemaining()){
   byte[] triangle=new byte[60];in.get(triangle);FloatBuffer v=ByteBuffer.wrap(triangle).order(ByteOrder.LITTLE_ENDIAN).asFloatBuffer().asReadOnlyBuffer();
   write(out,v,false);write(out,v,Boolean.parseBoolean(args[2]));
  }
  Files.write(Paths.get(args[1]),out.array());
 }
}
"""
for name,plane in [('before',out/'before-NativeTexturePlane.java'),('after',source/'java/org/codex/nfsugpreview/NativeTexturePlane.java')]:
 folder=out/name;folder.mkdir(exist_ok=True);shutil.copy2(plane,folder/'NativeTexturePlane.java');(folder/'EmptyPlaneHostTest.java').write_text(runner)
 subprocess.run([str(jdk/'bin/javac.exe'),'-d',str(folder),str(folder/'NativeTexturePlane.java'),str(folder/'EmptyPlaneHostTest.java')],check=True,capture_output=True)
 subprocess.run([str(jdk/'bin/java.exe'),'-cp',str(folder),'org.codex.nfsugpreview.EmptyPlaneHostTest',str(out/'triangles.bin'),str(out/(name+'-planes.bin')),'true' if name=='after' else 'false'],check=True,capture_output=True)
before=(out/'before-planes.bin').read_bytes();after=(out/'after-planes.bin').read_bytes();assert len(after)==len(before)==len(inputs)*96
with os.add_dll_directory('C:/msys64/mingw64/bin'):dll=C.CDLL(str(base/'NFSUG-pc-empty-model-plane-tests/source-scene-empty-plane.dll'))
proof=json.loads((base/'NFSUG-pc-empty-model-plane-tests/empty-plane-build-report.json').read_text());assert proof['dll_sha256']==sha(base/'NFSUG-pc-empty-model-plane-tests/source-scene-empty-plane.dll') and proof['helper_sha256']==sha(pc/'empty_model_plane.h')
empty=dll.nf_pc_test_empty_plane;empty.argtypes=[C.POINTER(C.c_float),C.POINTER(C.c_float)];empty.restype=C.c_int;valid=recovered=rejected=0
for i,v in enumerate(inputs):
 old=before[i*96:i*96+48];strict=after[i*96:i*96+48];model=after[i*96+48:i*96+96];assert strict==old,('strict plane changed',i)
 if struct.unpack_from('<i',old)[0]:assert model==old;valid+=1
 else:
  plane=(C.c_float*11)();ok=empty((C.c_float*15)(*v),plane);assert struct.unpack_from('<i',model)[0]==ok,('PC guard differs',i)
  if ok:assert model[4:]==bytes(plane);recovered+=1
  else:rejected+=1
assert valid>0 and recovered>=3 and rejected>=40
assert 'new NativeTexturePlane(mesh.mesh(),vertex,mesh.model)' in (source/'java/org/codex/nfsugpreview/NativeSceneGpu.java').read_text()
report=dict(result='VERIFIED_ANDROID_MODEL_ONLY_EMPTY_PLANE_HOST_PARITY',triangles=len(inputs),unchanged_valid_plane_records=valid,model_only_zero_coverage_recoveries=recovered,retained_rejections=rejected,all_strict_world_plane_records_byte_exact=True,all_fallback_plane_bytes_match_verified_pc_helper=True,input_buffers_unchanged=True,frozen_inputs=frozen,source_sha256={n:sha(source/'java/org/codex/nfsugpreview'/n) for n in ['NativeTexturePlane.java','NativeSceneGpu.java']},pc_helper_sha256=sha(pc/'empty_model_plane.h'),script_sha256=sha(Path(__file__)),android_gpu_verified=False,full_scene_60fps=False,limits='Host JVM numerical/component check using frozen actual model vertices and malformed controls. No full Android native scene or device pixel-coverage proof yet.')
(out/'empty-plane-host-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
