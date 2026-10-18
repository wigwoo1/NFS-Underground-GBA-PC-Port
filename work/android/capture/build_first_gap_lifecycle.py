"""Append read-only classifier JNI to isolated staged sources; production remains intact."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess
here=Path(__file__).resolve().parent;root=here.parents[2];base=Path(r'C:\NFSUG-Workspace');parent=base/'NFSUG-Android-Native-Current-20261017/native';out=base/'NFSUG-Android-Native-Current-20261017/lifecycle-native';out.mkdir(exist_ok=True);src=out/'source';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
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
text=text.replace(entry,entry+trace)

reset='static void live_visibility_reset(void){';start=text.index(reset);brace=text.index('{',start);depth=0
for end in range(brace,len(text)):
 if text[end]=='{':depth+=1
 elif text[end]=='}':
  depth-=1
  if not depth:break
before=r"""
static uint64_t nf_diagnostic_lifecycle_rows[256][16];static unsigned nf_diagnostic_lifecycle_count,nf_diagnostic_lifecycle_overflow,nf_diagnostic_guest_pc;
static NFVisibilityResult nf_diagnostic_native_result,nf_diagnostic_original_result;
static uint64_t nf_diagnostic_compare_header[32];static uint8_t nf_diagnostic_query_ram[0x48000],nf_diagnostic_builder_ram[0x48000];static uint32_t nf_diagnostic_compare_registers[16];
static unsigned nf_diagnostic_attempt_mask,nf_diagnostic_success_mask;
static int nf_diagnostic_result(unsigned bit,int value){if(live_scene.serial==17){nf_diagnostic_attempt_mask|=1u<<bit;if(value)nf_diagnostic_success_mask|=1u<<bit;}return value;}
static void nf_diagnostic_model_pending(uint64_t*);
static void nf_diagnostic_lifecycle_record(unsigned kind,unsigned line){
 if(live_scene.serial!=17&&live_visibility.serial!=17)return;
 if(kind<3&&nf_diagnostic_guest_pc!=0x08002cb4&&nf_diagnostic_guest_pc!=0x03004c74&&nf_diagnostic_guest_pc!=0x03004d50)return;
 if(nf_diagnostic_lifecycle_count==256){nf_diagnostic_lifecycle_overflow++;return;}
 uint64_t*r=nf_diagnostic_lifecycle_rows[nf_diagnostic_lifecycle_count++];r[0]=kind;r[1]=line;r[2]=nf_diagnostic_guest_pc;r[3]=c?c->frameCounter(c):0;r[4]=live_scene_epoch;r[5]=live_scene.serial;r[6]=live_visibility.epoch;r[7]=live_visibility.serial;r[8]=live_visibility.stage;r[9]=live_visibility.pending!=NULL;r[10]=live_visibility.prepared;nf_diagnostic_model_pending(r);r[13]=live_visibility.stats[2];r[14]=live_visibility.query_frame;r[15]=live_visibility.builder_frame;
}
"""
after=r"""
static void nf_diagnostic_visibility_reset(unsigned line){nf_diagnostic_lifecycle_record(3,line);live_visibility_reset();}
"""
text=text[:start]+before+text[start:end+1]+after+text[end+1:]
model_reset='static void live_model_inputs_reset(void){';assert text.count(model_reset)==1
text=text.replace(model_reset,'static void nf_diagnostic_model_pending(uint64_t*r){r[11]=pending_model_inputs.count;r[12]=pending_model_inputs.failed;}\n'+model_reset)
# Replace only callers; the original definition and wrapper's direct call stay intact.
cut=text.index(after)+len(after);text=text[:cut]+text[cut:].replace('live_visibility_reset()','nf_diagnostic_visibility_reset(__LINE__)')
call=' live_visibility_event_detail(cpu,pc);';assert text.count(call)==1
text=text.replace(call,' nf_diagnostic_guest_pc=pc;nf_diagnostic_lifecycle_record(1,0);\n'+call+'\n nf_diagnostic_lifecycle_record(2,0);nf_diagnostic_guest_pc=0;')
condition='int ok=nf_visibility_snapshot_evaluate(live_visibility.pending,&native)&&native_surface_read(NULL,state,original.state,256)&&native_surface_read(NULL,rd32(state+0x60),original.queue,NF_VISIBILITY_QUEUE_BYTES)&&native_surface_read(NULL,rd32(state+0x64),original.groups,4096);';assert text.count(condition)==1
text=text.replace(condition,'if(live_scene.serial==17){nf_diagnostic_attempt_mask=nf_diagnostic_success_mask=0;}\n   int ok=nf_diagnostic_result(0,nf_visibility_snapshot_evaluate(live_visibility.pending,&native))&&nf_diagnostic_result(1,native_surface_read(NULL,state,original.state,256))&&nf_diagnostic_result(2,native_surface_read(NULL,rd32(state+0x60),original.queue,NF_VISIBILITY_QUEUE_BYTES))&&nf_diagnostic_result(3,native_surface_read(NULL,rd32(state+0x64),original.groups,4096));')
guard='if(!ok||memcmp(&native,&original,sizeof(native))){';guard_at=text.index(guard,text.index('nf_diagnostic_result(0,nf_visibility_snapshot_evaluate'))
snapshot=r"""
   if(live_scene.serial==17){
    memset(nf_diagnostic_compare_header,0,sizeof(nf_diagnostic_compare_header));uint64_t*h=nf_diagnostic_compare_header;
    h[0]=0x3143504e;h[1]=1;h[2]=256+2*sizeof(NFVisibilityResult)+2*0x48000+64;h[3]=sizeof(NFVisibilityResult);h[4]=live_scene_epoch;h[5]=live_scene.serial;h[6]=c->frameCounter(c);h[7]=ok;
    h[8]=offsetof(NFVisibilityResult,state);h[9]=sizeof(original.state);h[10]=offsetof(NFVisibilityResult,queue);h[11]=sizeof(original.queue);h[12]=offsetof(NFVisibilityResult,groups);h[13]=sizeof(original.groups);h[14]=offsetof(NFVisibilityResult,selected);h[15]=sizeof(original.selected);
    memcpy(nf_diagnostic_query_ram,live_visibility.ram,sizeof(nf_diagnostic_query_ram));h[16]=1;
    h[17]=(native_surface_read(NULL,0x02000000,nf_diagnostic_builder_ram,0x40000)?1:0)|(native_surface_read(NULL,0x03000000,nf_diagnostic_builder_ram+0x40000,0x8000)?2:0);
    h[18]=0x48000;h[19]=live_visibility.stage;h[20]=state;h[21]=live_visibility.query_frame;h[22]=nf_diagnostic_attempt_mask;h[23]=nf_diagnostic_success_mask;h[24]=NF_VISIBILITY_QUEUE_CAPACITY;h[25]=NF_VISIBILITY_QUEUE_BYTES;h[26]=live_visibility.prepared;
    memset(&nf_diagnostic_native_result,0,sizeof(nf_diagnostic_native_result));memset(&nf_diagnostic_original_result,0,sizeof(nf_diagnostic_original_result));
    if(nf_diagnostic_success_mask&1)memcpy(&nf_diagnostic_native_result,&native,sizeof(native));
    if(nf_diagnostic_success_mask&2)memcpy(nf_diagnostic_original_result.state,original.state,sizeof(original.state));
    if(nf_diagnostic_success_mask&4)memcpy(nf_diagnostic_original_result.queue,original.queue,sizeof(original.queue));
    if(nf_diagnostic_success_mask&8)memcpy(nf_diagnostic_original_result.groups,original.groups,sizeof(original.groups));
    nf_diagnostic_original_result.selected=original.selected;memcpy(nf_diagnostic_compare_registers,cpu->gprs,64);
   }
"""
text=text[:guard_at]+snapshot+text[guard_at:]

header.write_text(text)
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
observer+='\nsize_t nf_android_diagnostic_lifecycle(uint64_t*out,size_t capacity){size_t n=2+nf_diagnostic_lifecycle_count*16;if(!out)return n;if(capacity<n)return 0;out[0]=nf_diagnostic_lifecycle_count;out[1]=nf_diagnostic_lifecycle_overflow;memcpy(out+2,nf_diagnostic_lifecycle_rows,nf_diagnostic_lifecycle_count*16*8);return n;}\nsize_t nf_android_diagnostic_comparison(void*out,size_t capacity){size_t n=256+2*sizeof(NFVisibilityResult)+2*0x48000+64;if(!out)return n;if(capacity<n)return 0;uint8_t*p=out;memcpy(p,nf_diagnostic_compare_header,256);p+=256;memcpy(p,&nf_diagnostic_native_result,sizeof(NFVisibilityResult));p+=sizeof(NFVisibilityResult);memcpy(p,&nf_diagnostic_original_result,sizeof(NFVisibilityResult));p+=sizeof(NFVisibilityResult);memcpy(p,nf_diagnostic_query_ram,0x48000);p+=0x48000;memcpy(p,nf_diagnostic_builder_ram,0x48000);p+=0x48000;memcpy(p,nf_diagnostic_compare_registers,64);return n;}\n'
jni=r"""
int nf_android_diagnostic_classify_world(uint64_t,unsigned,unsigned,unsigned,uint64_t[32]);
JNIEXPORT jlongArray JNICALL Java_org_codex_nfsugpreview_NativeClassifiedGapInstrumentation_classifyWorld(JNIEnv*e,jclass cls,jlong h,jlong epoch,jint serial,jint begin,jint end){
 (void)cls;uint64_t timing[4],data[32];if(!nfa_core_timing(handle(h),timing)||!nf_android_diagnostic_classify_world((uint64_t)epoch,(unsigned)serial,(unsigned)begin,(unsigned)end,data))return NULL;
 jlong values[32];for(unsigned i=0;i<32;i++)values[i]=(jlong)data[i];jlongArray out=(*e)->NewLongArray(e,32);if(out)(*e)->SetLongArrayRegion(e,out,0,32,values);return out;
}
"""
jni+='\nsize_t nf_android_diagnostic_lifecycle(uint64_t*,size_t);size_t nf_android_diagnostic_comparison(void*,size_t);\nJNIEXPORT jlongArray JNICALL Java_org_codex_nfsugpreview_NativeClassifiedGapInstrumentation_lifecycleTrace(JNIEnv*e,jclass cls,jlong h){(void)cls;uint64_t timing[4];if(!nfa_core_timing(handle(h),timing))return NULL;size_t n=nf_android_diagnostic_lifecycle(NULL,0);uint64_t*data=malloc(n*8);if(!data)return NULL;if(nf_android_diagnostic_lifecycle(data,n)!=n){free(data);return NULL;}jlongArray out=(*e)->NewLongArray(e,(jsize)n);if(out)(*e)->SetLongArrayRegion(e,out,0,(jsize)n,(const jlong*)data);free(data);return out;}\nJNIEXPORT jbyteArray JNICALL Java_org_codex_nfsugpreview_NativeClassifiedGapInstrumentation_visibilityComparison(JNIEnv*e,jclass cls,jlong h){(void)cls;uint64_t timing[4];if(!nfa_core_timing(handle(h),timing))return NULL;size_t n=nf_android_diagnostic_comparison(NULL,0);void*data=malloc(n);if(!data)return NULL;if(nf_android_diagnostic_comparison(data,n)!=n){free(data);return NULL;}jbyteArray out=(*e)->NewByteArray(e,(jsize)n);if(out)(*e)->SetByteArrayRegion(e,out,0,(jsize)n,(const jbyte*)data);free(data);return out;}\n'
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
