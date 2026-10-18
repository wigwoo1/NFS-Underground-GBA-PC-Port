"""Isolated Android owned-text C ABI build; stable capture/JNI cache unchanged."""
from pathlib import Path
import subprocess,sys,json,hashlib,struct,argparse
p=argparse.ArgumentParser();p.add_argument("--jni",action="store_true");a=p.parse_args()
here=Path(__file__).resolve().parent;base=Path(r"C:\NFSUG-Workspace");out=base/('NFSUG-android-owned-text-jni-local' if a.jni else 'NFSUG-android-owned-text-ndk-local');source=out/'source';tools=base/'android-tools';ndk=tools/'android-ndk-r30';cmake=Path(r"C:\Program Files\CMake\bin\cmake.exe");ninja=tools/'python-tools/bin/ninja.exe';core=base/'NFSUG-android-local'
subprocess.run([sys.executable,str(here/'stage_capture.py'),'--output',str(out)],check=True)
inputs={}
for filename,extension in (('observer.c','owned_text_observer.inc'),('nfsug_android_core.c','owned_text_core.inc')):
 data=(here/extension).read_bytes();inputs[extension]=hashlib.sha256(data).hexdigest()
 with (source/filename).open('ab') as f:f.write(b'\n'+data)
for name in ('nfsug_capture.h','nfsug_owned_text.h'):(source/name).write_bytes((here/name).read_bytes())
if a.jni:
 data=(here/'owned_text_jni.inc').read_bytes();inputs['owned_text_jni.inc']=hashlib.sha256(data).hexdigest()
 with (source/'nfsug_android_jni.c').open('ab') as f:f.write(b'\n'+data)
targets=[]
for abi,machine in (('x86_64',62),('arm64-v8a',183)):
 build=out/('build-'+abi)
 for phase,args in [('configure',['-S',source,'-B',build,'-G','Ninja','-DCMAKE_MAKE_PROGRAM='+str(ninja),'-DCMAKE_TOOLCHAIN_FILE='+str(ndk/'build/cmake/android.toolchain.cmake'),'-DANDROID_ABI='+abi,'-DANDROID_PLATFORM=android-26','-DCMAKE_BUILD_TYPE=Release','-DNF_CAPTURE_JNI='+('ON' if a.jni else 'OFF'),'-DNF_MGBA_SOURCE='+str(core/'mgba-source'),'-DNF_MGBA_BUILD='+str(core/('build-'+abi))]),('build',['--build',build,'--parallel','4'])]:
  with (out/(phase+'-'+abi+'.log')).open('w') as log:subprocess.run([str(cmake),*map(str,args)],check=True,stdout=log,stderr=subprocess.STDOUT)
  print(phase+' '+abi+' PASS',flush=True)
 lib=build/('libnfsug_android_core.so' if a.jni else 'libnfsug_android_capture.so');data=lib.read_bytes();assert data[:6]==b'\x7fELF\x02\x01' and struct.unpack_from('<HH',data,16)==(3,machine)
 symbols=subprocess.run([str(ndk/'toolchains/llvm/prebuilt/windows-x86_64/bin/llvm-readelf.exe'),'--dyn-syms','--wide',str(lib)],check=True,capture_output=True,text=True).stdout
 defined={r.split()[7] for r in symbols.splitlines() if len(r.split())>=8 and r.split()[3]=='FUNC' and r.split()[6]!='UND'}
 assert {'nfa_core_capture_text_enable','nfa_core_capture_text','nfa_core_capture_menu_text','nfa_core_capture_menu_text_bundle'}<=defined
 if a.jni:assert {'Java_org_codex_nfsugpreview_NativeMenuCapture_enableNative','Java_org_codex_nfsugpreview_NativeMenuCapture_bundleNative'}<=defined
 assert not {'nf_owned_text_diagnostic','nf_owned_text_trace','nf_owned_text_glyph_count','nf_frame','nf_dt','nf_pace'}&defined
 offset=struct.unpack_from('<Q',data,32)[0];stride,count=struct.unpack_from('<HH',data,54);aligns=[struct.unpack_from('<II6Q',data,offset+i*stride)[-1] for i in range(count) if struct.unpack_from('<I',data,offset+i*stride)[0]==1];assert aligns and min(aligns)>=16384
 targets.append(dict(abi=abi,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),library=str(lib.relative_to(out)),machine=machine,alignments=aligns));(out/('exports-'+abi+'.log')).write_text(symbols)
report=dict(result='PASS_OWNED_TEXT_ANDROID_C_ABI_BUILD',targets=targets,extension_sha256=inputs,jni=a.jni,android_runtime=False,stable_cache_changed=False);(out/'owned-text-android-build-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))

if a.jni:
 project=here.parents[2];native_inputs={}
 for name in ('nfsug_android_core.c','nfsug_android_core.h','nfsug_android_jni.c'):
  native_inputs['work/android/'+name]=hashlib.sha256((project/'work/android'/name).read_bytes()).hexdigest()
 for f in here.iterdir():
  if f.is_file():native_inputs['work/android/capture/'+f.name]=hashlib.sha256(f.read_bytes()).hexdigest()
 report['native_inputs']=native_inputs
 (out/'capture-jni-build-report.json').write_text(json.dumps(report,indent=2))
