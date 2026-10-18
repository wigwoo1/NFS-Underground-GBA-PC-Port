"""Append read-only classifier JNI to isolated staged sources; production remains intact."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess
here=Path(__file__).resolve().parent;root=here.parents[2];base=Path(r'C:\NFSUG-Workspace');parent=base/'NFSUG-Android-Native-Wide-20261017/native';out=base/'NFSUG-Android-Native-Wide-20261017/background-probe-native';out.mkdir(exist_ok=True);src=out/'source';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
reference=json.loads((parent/'capture-jni-build-report.json').read_text());assert reference['jni']
for name,h in reference['native_inputs'].items():
 if name.endswith(('.c','.h','.inc','CMakeLists.txt','/stage_capture.py','/build_capture.py')):assert sha(root/name)==h,name
shutil.copytree(parent/'source',src,dirs_exist_ok=True)
jni=r"""
/* Read-only existing capture APIs, no observer event or acceptance changes. */
JNIEXPORT jlongArray JNICALL Java_org_codex_nfsugpreview_NativeClassifiedGapInstrumentation_backgroundProbe(JNIEnv*e,jclass cls,jlong h){
 (void)cls;uint64_t v[64]={0},stats[8]={0},t[4]={0},info[5]={0};NFAAndroidCore*core=handle(h);
 if(!nfa_core_timing(core,t)||!nfa_core_capture_stats(core,stats)||!t[2])return NULL;
 v[0]=0x3147424e;v[1]=1;for(unsigned i=0;i<4;i++)v[2+i]=t[i];
 v[6]=nfa_core_capture_layer_info(core,info)!=0;for(unsigned i=0;i<5;i++)v[7+i]=info[i];
 uint64_t epoch=stats[1];unsigned refresh=(unsigned)(t[2]-1);v[12]=epoch;v[13]=refresh;
 v[14]=nfa_core_capture_pair(core,refresh,&v[15])!=0;
 v[23]=nfa_core_capture_split(core,refresh,&v[24])!=0;
 v[36]=nfa_core_capture_display_owner(core,refresh,&v[37])!=0;
 v[45]=nfa_core_capture_provenance(core,epoch,refresh,NULL,0);
 v[46]=nfa_core_capture_bundle(core,epoch,refresh,NULL,0);
 v[47]=nfa_core_capture_sky(core,epoch,refresh,NULL,0);
 v[48]=nfa_core_capture_sky_scene(core,epoch,refresh,NULL,0);
 v[49]=nfa_core_capture_background_scene(core,epoch,refresh,NULL,0);
 if(v[6]){v[50]=nfa_core_capture_bundle(core,info[0],(unsigned)info[1],NULL,0);v[51]=nfa_core_capture_background_scene(core,info[0],(unsigned)info[1],NULL,0);}
 if(!nfa_core_timing(core,t))return NULL;for(unsigned i=0;i<4;i++)v[52+i]=t[i];
 if(!nfa_core_capture_stats(core,stats))return NULL;for(unsigned i=0;i<8;i++)v[56+i]=stats[i];
 jlong values[64];for(unsigned i=0;i<64;i++)values[i]=(jlong)v[i];jlongArray out=(*e)->NewLongArray(e,64);if(out)(*e)->SetLongArrayRegion(e,out,0,64,values);return out;
}
JNIEXPORT jbyteArray JNICALL Java_org_codex_nfsugpreview_NativeClassifiedGapInstrumentation_backgroundProvenance(JNIEnv*e,jclass cls,jlong h){
 (void)cls;uint64_t t[4],stats[8];NFAAndroidCore*core=handle(h);if(!nfa_core_timing(core,t)||!nfa_core_capture_stats(core,stats)||!t[2])return NULL;
 unsigned refresh=(unsigned)(t[2]-1);size_t bytes=nfa_core_capture_provenance(core,stats[1],refresh,NULL,0);if(!bytes||bytes>65536)return NULL;
 void*data=malloc(bytes);if(!data)return NULL;if(nfa_core_capture_provenance(core,stats[1],refresh,data,bytes)!=bytes){free(data);return NULL;}
 jbyteArray out=(*e)->NewByteArray(e,(jsize)bytes);if(out)(*e)->SetByteArrayRegion(e,out,0,(jsize)bytes,(const jbyte*)data);free(data);return out;
}
"""
with (src/'nfsug_android_jni.c').open('a',encoding='utf8') as f:f.write(jni)
assert sha(src/'observer.c')==sha(parent/'source/observer.c')
assert sha(src/'camera/live_visibility.h')==sha(parent/'source/camera/live_visibility.h')
cmake=Path(r'C:\Program Files\CMake\bin\cmake.exe');ndk=base/'android-tools/android-ndk-r30';ninja=base/'android-tools/python-tools/bin/ninja.exe';core=base/'NFSUG-android-local';build=out/'build-jni-x86_64'
commands=[[str(cmake),'-S',str(src),'-B',str(build),'-G','Ninja','-DCMAKE_MAKE_PROGRAM='+str(ninja),'-DCMAKE_TOOLCHAIN_FILE='+str(ndk/'build/cmake/android.toolchain.cmake'),'-DANDROID_ABI=x86_64','-DANDROID_PLATFORM=android-26','-DCMAKE_BUILD_TYPE=Release','-DNF_CAPTURE_JNI=ON','-DNF_VISIBILITY_QUEUE_CAPACITY=64','-DNF_MGBA_SOURCE='+str(core/'mgba-source'),'-DNF_MGBA_BUILD='+str(core/'build-x86_64')],[str(cmake),'--build',str(build),'--parallel','4']]
env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
for label,command in zip(['configure','compile'],commands):
 with (out/(label+'.log')).open('w') as log:subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
 print(label+' passed',flush=True)
targets=[]
for row in reference['targets']:
 r=dict(row);lib=out/r['library']
 if r['abi']=='x86_64':
  symbols=subprocess.run([str(ndk/'toolchains/llvm/prebuilt/windows-x86_64/bin/llvm-readelf.exe'),'--dyn-syms','--wide',str(lib)],check=True,capture_output=True,text=True).stdout;assert 'Java_org_codex_nfsugpreview_NativeClassifiedGapInstrumentation_backgroundProbe' in symbols;(out/'diagnostic-exports.log').write_text(symbols);r.update(bytes=lib.stat().st_size,sha256=sha(lib),diagnostic_api=True)
 else:lib.parent.mkdir(exist_ok=True);shutil.copy2(parent/r['library'],lib);assert sha(lib)==r['sha256'];r['diagnostic_api']=False
 targets.append(r)
report=dict(reference);report.update(result='BUILT_ISOLATED_WIDE_BACKGROUND_API_DIAGNOSTIC',diagnostic_only=True,diagnostic_supported_abi='x86_64',targets=targets,parent_native_report_sha256=sha(parent/'capture-jni-build-report.json'),factory_sha256=sha(Path(__file__)),staged_diagnostic_sha256={n:sha(src/n) for n in ['observer.c','nfsug_android_jni.c','camera/live_visibility.h']},commands=commands,logic_or_rejection_changed=False)
(out/'capture-jni-build-report.json').write_text(json.dumps(report,indent=2));print('BUILT_DIAGNOSTIC_CLASSIFIER_NO_RUNTIME_FIX',targets[0]['sha256'])
