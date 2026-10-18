"""Append read-only classifier JNI to isolated staged sources; production remains intact."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess
here=Path(__file__).resolve().parent;root=here.parents[2];base=Path(r'C:\NFSUG-Workspace');parent=base/'NFSUG-Android-Native-Wide-20261017/native';out=base/'NFSUG-Android-Native-Wide-20261017/byteproof-native';out.mkdir(exist_ok=True);src=out/'source';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
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

jni+=r"""
void nf_native_scene_rejection_detail(uint32_t out[9]);
void nf_native_scene_first_bad(uint32_t out[9]);
void nf_native_model_rejection_detail(uint32_t out[8]);
void nf_native_scene_model_rejection_visits(uint32_t out[113]);
JNIEXPORT jlongArray JNICALL Java_org_codex_nfsugpreview_NativeClassifiedGapInstrumentation_packetRejection(JNIEnv*e,jclass cls,jlong h){
 (void)cls;uint64_t t[4],stats[8];uint32_t detail[9]={0},bad[9]={0},model[8]={0},visits[113]={0};
 if(!nfa_core_timing(handle(h),t)||!nfa_core_capture_stats(handle(h),stats))return NULL;
 nf_native_scene_rejection_detail(detail);nf_native_scene_first_bad(bad);nf_native_model_rejection_detail(model);nf_native_scene_model_rejection_visits(visits);
 jlong values[153]={0};unsigned at=0;values[at++]=0x3152504e;values[at++]=1;
 for(unsigned i=0;i<4;i++)values[at++]=(jlong)t[i];for(unsigned i=0;i<8;i++)values[at++]=(jlong)stats[i];
 for(unsigned i=0;i<9;i++)values[at++]=detail[i];for(unsigned i=0;i<9;i++)values[at++]=bad[i];for(unsigned i=0;i<8;i++)values[at++]=model[i];for(unsigned i=0;i<113;i++)values[at++]=visits[i];
 if(at!=153)return NULL;jlongArray out=(*e)->NewLongArray(e,153);if(out)(*e)->SetLongArrayRegion(e,out,0,153,values);return out;
}
"""

header=src/'camera/live_visibility.h';text=header.read_text();start=text.index('static int live_native_model_assemble(');end=text.index('static void live_native_context_extract_event(',start);original=text[start:end];body=original
body=body.replace('){\n','){\n int diagnostic_target=live_scene.serial==114&&c->frameCounter(c)==12359&&object==0x02004458;\n if(diagnostic_target){uint64_t*d=nf_diagnostic_model_assembly;d[0]=0x31414d4e;d[1]=1;d[2]++;d[3]=1;d[4]=live_scene_epoch;d[5]=live_scene.serial;d[6]=live_scene.begin;d[7]=c->frameCounter(c);d[8]=context;d[9]=camera;d[10]=object;d[11]=live_surface_audit.enabled;d[12]=live_object_model_context.verified;d[13]=live_object_model_context.address;d[14]=live_object_model_context.object;d[15]=live_object_model_context.epoch;d[16]=live_object_model_context.serial;d[17]=live_object_model_context.frame;d[18]=live_object_model_context.active;d[19]=live_object_model_context.expected;d[20]=live_owned_model.ready;d[21]=live_owned_model.epoch;for(unsigned i=0;i<3;i++)d[22+i]=live_owned_model.args[i];d[25]=rotation&&memcmp(live_owned_model.rotation,rotation,48)==0;d[26]=live_owned_model.count;d[27]=live_owned_model.used;d[28]=live_owned_model.size;d[29]=live_owned_model.hash;d[30]=live_native_context_matches(context,object,live_scene_epoch,live_scene.serial,c->frameCounter(c));for(unsigned i=0;i<6;i++)d[34+i]=live_object_model_context.stats[i];for(unsigned i=0;i<3;i++)d[40+i]=live_native_model_assembly_stats[i];for(unsigned i=0;i<2;i++)d[43+i]=live_owned_model_assembly_stats[i];}\n',1)
needle='if(!live_native_context_matches(context,object,live_scene_epoch,live_scene.serial,c->frameCounter(c))){';assert body.count(needle)==1;body=body.replace(needle,needle+'if(diagnostic_target)nf_diagnostic_model_assembly[3]=2;')
needle='||memcmp(live_owned_model.rotation,rotation,48)){';assert body.count(needle)==1;body=body.replace(needle,needle+'if(diagnostic_target)nf_diagnostic_model_assembly[3]=3;')
needle='int ok=nf_extract_model(live_owned_model_read,NULL,context,camera,object,rotation,model,size);';assert body.count(needle)==1;body=body.replace(needle,needle+'if(diagnostic_target){nf_diagnostic_model_assembly[3]=4;nf_diagnostic_model_assembly[31]=ok!=0;nf_diagnostic_model_assembly[32]=model&&*model;nf_diagnostic_model_assembly[33]=size?*size:0;}')
assert body!=original
text=text[:start]+'static uint64_t nf_diagnostic_model_assembly[48];\n'+body+text[end:];header.write_text(text)
observer_extra=r"""
int nf_android_diagnostic_model_assembly(uint64_t out[48]){if(!c||!out)return 0;memcpy(out,nf_diagnostic_model_assembly,48*sizeof(uint64_t));return 1;}
"""
with (src/'observer.c').open('a',encoding='utf8') as f:f.write(observer_extra)
jni+=r"""
int nf_android_diagnostic_model_assembly(uint64_t out[48]);
JNIEXPORT jlongArray JNICALL Java_org_codex_nfsugpreview_NativeClassifiedGapInstrumentation_modelAssembly(JNIEnv*e,jclass cls,jlong h){
 (void)cls;uint64_t t[4],raw[48];if(!nfa_core_timing(handle(h),t)||!nf_android_diagnostic_model_assembly(raw))return NULL;jlong values[48];for(unsigned i=0;i<48;i++)values[i]=(jlong)raw[i];jlongArray out=(*e)->NewLongArray(e,48);if(out)(*e)->SetLongArrayRegion(e,out,0,48,values);return out;
}
"""

header=src/'camera/live_visibility.h';text=header.read_text();helper='\nstatic uint8_t*nf_diagnostic_model_byteproof;static size_t nf_diagnostic_model_byteproof_size;\nstatic void nf_diag_model_byteproof_capture(unsigned context,unsigned camera,unsigned object,const int32_t*rotation){\n if(nf_diagnostic_model_byteproof||live_owned_model.count>128||live_owned_model.used>262144)return;\n uint64_t h[64]={0};uint8_t actual_context[68]={0};unsigned count=live_owned_model.count,used=live_owned_model.used;\n h[0]=0x31424d4e;h[1]=1;h[3]=live_scene_epoch;h[4]=live_scene.serial;h[5]=live_scene.begin;h[6]=c->frameCounter(c);h[7]=context;h[8]=camera;h[9]=object;h[10]=live_object_model_context.frame;\n h[11]=native_surface_read(NULL,context,actual_context,68)!=0;h[12]=h[11]&&!memcmp(actual_context,live_object_model_context.context,68);h[13]=count;h[14]=used;h[15]=h[16]=h[17]=1;\n uint8_t*actual=calloc(used?used:1,1);if(!actual)return;\n for(unsigned i=0;i<count;i++){uint32_t*b=live_owned_model.blocks[i];if(b[2]>used||b[1]>used-b[2]||(uint64_t)b[0]+b[1]>0x100000000ull){h[15]=0;if(!h[18])h[18]=i+1;continue;}\n  if(!native_surface_read(NULL,b[0],actual+b[2],b[1])){h[16]=0;if(!h[18])h[18]=i+1;continue;}\n  for(unsigned j=0;j<b[1];j++)if(actual[b[2]+j]!=live_owned_model.bytes[b[2]+j]){h[17]=0;h[19]++;if(!h[18])h[18]=i+1;}\n }\n void*owned=NULL,*original=NULL;size_t owned_size=0,original_size=0;\n h[20]=nf_extract_model(live_owned_model_read,NULL,context,camera,object,rotation,&owned,&owned_size)!=0;\n h[21]=nf_extract_model(native_surface_read,NULL,context,camera,object,rotation,&original,&original_size)!=0;\n h[22]=h[20]&&h[21]&&owned_size==original_size&&!memcmp(owned,original,owned_size);h[23]=owned_size;h[24]=original_size;\n if(h[20])h[26]=surface_audit_hash(owned,owned_size);if(h[21])h[27]=surface_audit_hash(original,original_size);h[25]=h[20]&&owned_size==live_owned_model.size&&h[26]==live_owned_model.hash;\n const void*parts[8]={live_object_model_context.context,actual_context,rotation,live_owned_model.blocks,live_owned_model.bytes,actual,owned,original};size_t sizes[8]={68,68,48,count*12u,used,used,owned_size,original_size};size_t total=sizeof(h);int valid=1;\n for(unsigned i=0;i<8;i++){if(sizes[i]>4u*1024u*1024u-total){valid=0;break;}h[32+i*2]=total;h[33+i*2]=sizes[i];total+=sizes[i];}h[2]=total;\n if(valid){uint8_t*out=malloc(total);if(out){memcpy(out,h,sizeof(h));for(unsigned i=0;i<8;i++)if(sizes[i])memcpy(out+h[32+i*2],parts[i],sizes[i]);nf_diagnostic_model_byteproof=out;nf_diagnostic_model_byteproof_size=total;}}\n free(actual);nf_surface_free(owned);nf_surface_free(original);\n}\n'
marker='static uint64_t nf_diagnostic_model_assembly[48];';assert text.count(marker)==1;text=text.replace(marker,helper+'\n'+marker)
marker=' if(!live_surface_audit.enabled)return nf_extract_model(native_surface_read,NULL,context,camera,object,rotation,model,size);';assert text.count(marker)==1;text=text.replace(marker,' if(diagnostic_target)nf_diag_model_byteproof_capture(context,camera,object,rotation);\n'+marker);header.write_text(text)
with (src/'observer.c').open('a',encoding='utf8') as f:f.write(r"""
size_t nf_android_diagnostic_model_byteproof(void*out,size_t capacity){if(!c||!nf_diagnostic_model_byteproof)return 0;if(!out)return nf_diagnostic_model_byteproof_size;if(capacity<nf_diagnostic_model_byteproof_size)return 0;memcpy(out,nf_diagnostic_model_byteproof,nf_diagnostic_model_byteproof_size);return nf_diagnostic_model_byteproof_size;}
""")
jni+=r"""
size_t nf_android_diagnostic_model_byteproof(void*,size_t);
JNIEXPORT jbyteArray JNICALL Java_org_codex_nfsugpreview_NativeClassifiedGapInstrumentation_modelByteproof(JNIEnv*e,jclass cls,jlong h){
 (void)cls;uint64_t t[4];if(!nfa_core_timing(handle(h),t))return NULL;size_t bytes=nf_android_diagnostic_model_byteproof(NULL,0);if(!bytes||bytes>4u*1024u*1024u)return NULL;void*copy=malloc(bytes);if(!copy)return NULL;if(nf_android_diagnostic_model_byteproof(copy,bytes)!=bytes){free(copy);return NULL;}jbyteArray out=(*e)->NewByteArray(e,(jsize)bytes);if(out)(*e)->SetByteArrayRegion(e,out,0,(jsize)bytes,copy);free(copy);return out;
}
"""
with (src/'nfsug_android_jni.c').open('a',encoding='utf8') as f:f.write(jni)
assert (src/'observer.c').read_text().startswith((parent/'source/observer.c').read_text())
assert sha(src/'nfsug_android_core.c')==sha(parent/'source/nfsug_android_core.c')
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
report=dict(reference);report.update(result='BUILT_ISOLATED_WIDE_MODEL_BYTEPROOF_DIAGNOSTIC',diagnostic_only=True,diagnostic_supported_abi='x86_64',targets=targets,parent_native_report_sha256=sha(parent/'capture-jni-build-report.json'),factory_sha256=sha(Path(__file__)),staged_diagnostic_sha256={n:sha(src/n) for n in ['observer.c','nfsug_android_jni.c','camera/live_visibility.h']},commands=commands,logic_or_rejection_changed=False)
(out/'capture-jni-build-report.json').write_text(json.dumps(report,indent=2));print('BUILT_DIAGNOSTIC_CLASSIFIER_NO_RUNTIME_FIX',targets[0]['sha256'])
