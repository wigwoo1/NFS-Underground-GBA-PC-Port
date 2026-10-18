"""Append read-only classifier JNI to isolated staged sources; production remains intact."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess
here=Path(__file__).resolve().parent;root=here.parents[2];base=Path(r'C:\NFSUG-Workspace');parent=base/'NFSUG-Android-Native-Current-20261017/native';out=base/'NFSUG-Android-Native-Current-20261017/classified-native';out.mkdir(exist_ok=True);src=out/'source';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
reference=json.loads((parent/'capture-jni-build-report.json').read_text());assert reference['jni']
for name,h in reference['native_inputs'].items():
 if name.endswith(('.c','.h','.inc','CMakeLists.txt','/stage_capture.py','/build_capture.py')):assert sha(root/name)==h,name
shutil.copytree(parent/'source',src,dirs_exist_ok=True)
header=src/'camera/live_visibility.h';text=header.read_text()
declaration='static void live_model_inputs_reset(void){';assert text.count(declaration)==1
text=text.replace(declaration,'static uint64_t nf_diagnostic_packet_guard[NF_COMPLETED_SURFACE_HISTORY][12];\n'+declaration)
entry='static void live_visibility_packet(const void*data,size_t size){';assert text.count(entry)==1
trace=r"""
 NFScenePacket diagnostic_packet;uint32_t raw_header[7]={0};
 if(data&&size>=sizeof(raw_header))memcpy(raw_header,data,sizeof(raw_header));
 int decode_ok=data&&nf_scene_packet_view(data,size,&diagnostic_packet);
 if(raw_header[0]==0x3150534eu){
  uint64_t*row=nf_diagnostic_packet_guard[raw_header[4]%NF_COMPLETED_SURFACE_HISTORY];
  row[0]=raw_header[4];row[1]=raw_header[5];row[2]=raw_header[6];row[3]=live_scene_epoch;row[4]=c?c->frameCounter(c):0;row[5]=live_visibility.stage;row[6]=live_visibility.history!=NULL;row[7]=live_visibility.epoch;row[8]=live_visibility.serial;row[9]=decode_ok!=0;row[10]=pending_model_inputs.count;row[11]=pending_model_inputs.failed;
 }
"""
text=text.replace(entry,entry+trace);header.write_text(text)
observer=r"""
/* Observation only: exact same classifier, original rejection remains intact. */
int nf_android_diagnostic_classify_world(uint64_t epoch,unsigned serial,unsigned begin,unsigned end,uint64_t out[32]){
 if(!c||!android_source_world||!out)return 0;
 memset(out,0,32*sizeof(*out));void*packet=NULL;size_t bytes=0;unsigned stage=999,count=0;
 int ok=nf_live_completed_native_multimodel_world_classified_owned(epoch,serial,begin,end,&packet,&bytes,&stage);
 out[0]=ok!=0;out[1]=stage;out[2]=bytes;out[3]=nf_live_completed_models_count(epoch,serial,begin,end,&count)!=0;out[4]=count;out[5]=live_scene_epoch;out[6]=c->frameCounter(c);
 for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++){
  NFCompletedSurfaceAudit*entry=completed_surface_audit[i];
  if(entry&&entry->id.epoch==epoch&&entry->id.serial==serial&&entry->id.begin_refresh==begin&&entry->id.end_refresh==end){uint32_t view[12];out[7]=i+1;out[8]=nf_visibility_snapshot_prepared_view(entry->render_snapshot,view)!=0;}
 }
 NFVisibilityPoseInputs pose;out[9]=nf_live_completed_visibility_pose(epoch,serial,begin,end,&pose)!=0;
 for(unsigned i=0;i<live_palettes.count;i++)if(live_palettes.entries[i].epoch==epoch&&live_palettes.entries[i].serial==serial&&live_palettes.entries[i].begin==begin&&live_palettes.entries[i].end==end&&live_palettes.entries[i].bank)out[10]=1;
 unsigned slot=serial%NF_COMPLETED_SURFACE_HISTORY;
 out[11]=completed_model_inputs[slot].valid;out[12]=completed_model_inputs[slot].count;out[13]=completed_model_inputs[slot].id.epoch;out[14]=completed_model_inputs[slot].id.serial;out[15]=completed_model_inputs[slot].id.begin_refresh;out[16]=completed_model_inputs[slot].id.end_refresh;out[17]=NF_COMPLETED_SURFACE_HISTORY;out[18]=pending_model_inputs.count;out[19]=pending_model_inputs.failed;
 for(unsigned i=0;i<12;i++)out[20+i]=nf_diagnostic_packet_guard[slot][i];
 if(packet)nf_scene_packet_free(packet);return 1;
}
"""
jni=r"""
int nf_android_diagnostic_classify_world(uint64_t,unsigned,unsigned,unsigned,uint64_t[32]);
JNIEXPORT jlongArray JNICALL Java_org_codex_nfsugpreview_NativeClassifiedGapInstrumentation_classifyWorld(JNIEnv*e,jclass cls,jlong h,jlong epoch,jint serial,jint begin,jint end){
 (void)cls;uint64_t timing[4],data[32];if(!nfa_core_timing(handle(h),timing)||!nf_android_diagnostic_classify_world((uint64_t)epoch,(unsigned)serial,(unsigned)begin,(unsigned)end,data))return NULL;
 jlong values[32];for(unsigned i=0;i<32;i++)values[i]=(jlong)data[i];jlongArray out=(*e)->NewLongArray(e,32);if(out)(*e)->SetLongArrayRegion(e,out,0,32,values);return out;
}
"""
for name,extra in [('observer.c',observer),('nfsug_android_jni.c',jni)]:
 with (src/name).open('a',encoding='utf8') as f:f.write(extra)
cmake=Path(r'C:\Program Files\CMake\bin\cmake.exe');ndk=base/'android-tools/android-ndk-r30';ninja=base/'android-tools/python-tools/bin/ninja.exe';core=base/'NFSUG-android-local';build=out/'build-jni-x86_64'
commands=[[str(cmake),'-S',str(src),'-B',str(build),'-G','Ninja','-DCMAKE_MAKE_PROGRAM='+str(ninja),'-DCMAKE_TOOLCHAIN_FILE='+str(ndk/'build/cmake/android.toolchain.cmake'),'-DANDROID_ABI=x86_64','-DANDROID_PLATFORM=android-26','-DCMAKE_BUILD_TYPE=Release','-DNF_CAPTURE_JNI=ON','-DNF_VISIBILITY_QUEUE_CAPACITY=20','-DNF_MGBA_SOURCE='+str(core/'mgba-source'),'-DNF_MGBA_BUILD='+str(core/'build-x86_64')],[str(cmake),'--build',str(build),'--parallel','4']]
env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
for label,command in zip(['configure','compile'],commands):
 with (out/(label+'.log')).open('w') as log:subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
 print(label+' passed',flush=True)
targets=[]
for row in reference['targets']:
 r=dict(row);lib=out/r['library']
 if r['abi']=='x86_64':
  symbols=subprocess.run([str(ndk/'toolchains/llvm/prebuilt/windows-x86_64/bin/llvm-readelf.exe'),'--dyn-syms','--wide',str(lib)],check=True,capture_output=True,text=True).stdout;assert 'Java_org_codex_nfsugpreview_NativeClassifiedGapInstrumentation_classifyWorld' in symbols;(out/'diagnostic-exports.log').write_text(symbols);r.update(bytes=lib.stat().st_size,sha256=sha(lib),diagnostic_api=True)
 else:lib.parent.mkdir(exist_ok=True);shutil.copy2(parent/r['library'],lib);assert sha(lib)==r['sha256'];r['diagnostic_api']=False
 targets.append(r)
report=dict(reference);report.update(result='BUILT_ISOLATED_FIRST_GAP_CLASSIFIER_DIAGNOSTIC',diagnostic_only=True,diagnostic_supported_abi='x86_64',targets=targets,parent_native_report_sha256=sha(parent/'capture-jni-build-report.json'),factory_sha256=sha(Path(__file__)),staged_diagnostic_sha256={n:sha(src/n) for n in ['observer.c','nfsug_android_jni.c','camera/live_visibility.h']},commands=commands,logic_or_rejection_changed=False)
(out/'capture-jni-build-report.json').write_text(json.dumps(report,indent=2));print('BUILT_DIAGNOSTIC_CLASSIFIER_NO_RUNTIME_FIX',targets[0]['sha256'])
