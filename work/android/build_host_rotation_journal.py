from pathlib import Path
import hashlib,json,os,shutil,subprocess
root=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');base=Path(r'C:\NFSUG-Workspace');parent=base/'NFSUG-Android-Context-Refresh-20261017/native';out=base/'NFSUG-Host-Rotation-Journal-20261017';out.mkdir(exist_ok=True);src=out/'source';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
shutil.copytree(parent/'source',src,dirs_exist_ok=True);header=src/'camera/live_scene.h';text=header.read_text();original=text
names=['nf_native_scene_rejection_detail','nf_native_scene_first_bad','nf_native_model_rejection_detail','nf_native_scene_model_rejection_visits']
for name in names:
 needle='API void '+name+'(';assert text.count(needle)==1;text=text.replace(needle,'__declspec(dllexport) void '+name+'(')
assert all(text.count('__declspec(dllexport) void '+name+'(')==1 for name in names);header.write_text(text)
restored=text
for name in names:restored=restored.replace('__declspec(dllexport) void '+name+'(','API void '+name+'(')
assert restored==original

header=src/'camera/live_scene.h';text=header.read_text();text='static void nf_host_first_missing_capture(unsigned);\n'+text
needle='if(r[0]==1){if(r[4]!=live_scene.context||!live_scene.model)live_scene_bad();';assert text.count(needle)==1;text=text.replace(needle,'if(r[0]==1){nf_host_first_missing_capture(r[4]);if(r[4]!=live_scene.context||!live_scene.model)live_scene_bad();');header.write_text(text)
observer=r"""
static uint64_t nf_host_first_missing[48];
static void nf_host_first_missing_capture(unsigned actual_context){
 if(live_scene.serial!=848||live_scene.object!=0x02005834||live_scene.model)return;
 uint64_t*d=nf_host_first_missing;d[0]=0x314d464e;d[1]=1;d[2]++;d[3]=live_scene_epoch;d[4]=live_scene.serial;d[5]=live_scene.begin;d[6]=c->frameCounter(c);d[7]=live_scene.context;d[8]=live_scene.camera;d[9]=live_scene.object;d[10]=actual_context;d[11]=live_scene.state;d[12]=live_scene.model!=NULL;for(unsigned i=0;i<8;i++)d[13+i]=live_model_detail[i];d[21]=live_object_model_context.verified;d[22]=live_object_model_context.address;d[23]=live_object_model_context.object;d[24]=live_object_model_context.epoch;d[25]=live_object_model_context.serial;d[26]=live_object_model_context.frame;d[27]=live_object_model_context.active;d[28]=live_object_model_context.expected;d[29]=live_owned_model.ready;d[30]=live_owned_model.epoch;for(unsigned i=0;i<3;i++)d[31+i]=live_owned_model.args[i];d[34]=live_owned_model.count;d[35]=live_owned_model.used;uint32_t state[5];nf_assembly_detail(live_scene.assembly,state);for(unsigned i=0;i<5;i++)d[36+i]=state[i];for(unsigned i=0;i<16;i++)if(live_scene.rotations[i].address==live_model_detail[2]){d[41]++;d[42]=i;d[43]=live_scene.rotations[i].frame;d[44]=live_scene.rotations[i].frame<live_scene.begin;}d[45]=live_model_detail[3];
}
__declspec(dllexport) void nf_host_first_missing_model_read(uint64_t out[48]){if(out)memcpy(out,nf_host_first_missing,sizeof(nf_host_first_missing));}
"""
with (src/'observer.c').open('a',encoding='utf8') as f:f.write(observer)

header=src/'camera/live_scene.h';text=header.read_text();text='static void nf_host_rotation_event(unsigned,unsigned,unsigned,unsigned,unsigned,unsigned,unsigned);\n'+text
needle='if(native_surface_read(NULL,r[0],live_scene.rotations[i].matrix,48)){live_scene.rotations[i].address=r[2];live_scene.rotations[i].frame=c->frameCounter(c);}return;'
assert text.count(needle)==1;text=text.replace(needle,'int diagnostic_read=native_surface_read(NULL,r[0],live_scene.rotations[i].matrix,48);nf_host_rotation_event(1,r[2],i,live_scene.rotations[i].address,live_scene.rotations[i].frame,diagnostic_read!=0,r[0]);if(diagnostic_read){live_scene.rotations[i].address=r[2];live_scene.rotations[i].frame=c->frameCounter(c);}return;')
needle='unsigned address=rd32(r[0]+60),frame=c->frameCounter(c);';assert text.count(needle)==1;text=text.replace(needle,needle+'nf_host_rotation_event(4,address,0,0,0,0,r[0]);')
needle='live_scene.rotations[i].address=0;break;';assert text.count(needle)==1;text=text.replace(needle,'nf_host_rotation_event(2,live_scene.rotations[i].address,i,live_scene.rotations[i].address,live_scene.rotations[i].frame,live_scene.model!=NULL,r[0]);'+needle)
needle='memset(live_scene.rotations,0,sizeof(live_scene.rotations));';assert text.count(needle)==1;text=text.replace(needle,'nf_host_rotation_event(5,0x0200c24c,0,0,0,0,0);'+needle);header.write_text(text)
observer=r"""
static uint64_t nf_host_rotation_counts[16],nf_host_rotation_first[16],nf_host_rotation_last[16],nf_host_rotation_consume[16],nf_host_rotation_rows[256][16];
static unsigned nf_host_rotation_count,nf_host_rotation_cursor,nf_host_rotation_dropped;
static void nf_host_rotation_event(unsigned kind,unsigned key,unsigned slot,unsigned old_key,unsigned old_frame,unsigned ok,unsigned source){
 if(!c)return;const unsigned target=0x0200c24c;unsigned frame=c->frameCounter(c);
 if(kind==1){nf_host_rotation_counts[4]++;if(key==target){nf_host_rotation_counts[5]++;if(nf_host_rotation_counts[5]==1)nf_host_rotation_counts[12]=frame;nf_host_rotation_counts[10]=frame;}if(old_key==target&&key!=target)nf_host_rotation_counts[7]++;}
 if(kind==2&&key==target){nf_host_rotation_counts[6]++;nf_host_rotation_counts[11]=frame;}
 if(kind==4&&key==target){nf_host_rotation_counts[8]++;if(nf_host_rotation_counts[8]==1)nf_host_rotation_counts[13]=frame;nf_host_rotation_counts[14]=frame;}
 if(kind==5)nf_host_rotation_counts[9]++;
 if(key!=target&&old_key!=target)return;
 uint64_t row[16]={kind,live_scene_epoch,live_scene.serial,live_scene.begin,frame,key,slot,old_key,old_frame,ok,source,live_scene.object,live_scene.context,live_scene.slot,0,0};
 for(unsigned i=0;i<16;i++)if(live_scene.rotations[i].address==target){row[14]++;if(live_scene.rotations[i].frame>=live_scene.begin&&live_scene.rotations[i].frame<=frame)row[15]++;}
 if(kind==1&&key==target){if(nf_host_rotation_counts[5]==1)memcpy(nf_host_rotation_first,row,sizeof(row));memcpy(nf_host_rotation_last,row,sizeof(row));}
 if(kind==2&&key==target)memcpy(nf_host_rotation_consume,row,sizeof(row));
 memcpy(nf_host_rotation_rows[nf_host_rotation_cursor],row,sizeof(row));nf_host_rotation_cursor=(nf_host_rotation_cursor+1)%256;if(nf_host_rotation_count<256)nf_host_rotation_count++;else nf_host_rotation_dropped++;
}
__declspec(dllexport) size_t nf_host_rotation_journal_read(uint64_t*out,size_t capacity){
 size_t words=64+nf_host_rotation_count*16;if(!out)return words;if(capacity<words)return 0;uint64_t header[16];memcpy(header,nf_host_rotation_counts,sizeof(header));header[0]=0x314a524e;header[1]=1;header[2]=nf_host_rotation_count;header[3]=nf_host_rotation_dropped;header[15]=0x0200c24c;memcpy(out,header,sizeof(header));memcpy(out+16,nf_host_rotation_first,128);memcpy(out+32,nf_host_rotation_last,128);memcpy(out+48,nf_host_rotation_consume,128);unsigned start=nf_host_rotation_count==256?nf_host_rotation_cursor:0;for(unsigned i=0;i<nf_host_rotation_count;i++)memcpy(out+64+i*16,nf_host_rotation_rows[(start+i)%256],128);return words;
}
"""
with (src/'observer.c').open('a',encoding='utf8') as f:f.write(observer)
provenance=json.loads((parent/'source-provenance.json').read_text());cpu=provenance['cpu_sources'];package=root/'work/v2/package/NFSUG-Native-Renderer-source'
lib=out/'capture-diagnostic-host.dll'
cmd=['C:/msys64/mingw64/bin/gcc.exe','-O2','-shared','-ffunction-sections','-fdata-sections','-DBUILD_STATIC','-DM_CORE_GBA','-DUSE_DEBUGGERS','-DNF_VISIBILITY_CAPTURE','-DNF_VISIBILITY_QUEUE_CAPACITY=64','-DNF_ROAD_ATTRIBUTE_CORRECTION','-DNF_PACKET_NO_FILES','-D_GNU_SOURCE','-I'+str(src),'-I'+str(src/'camera'),'-I'+str(package/'deps/mgba-0.10.5/include'),'-I'+str(package/'build/mgba-nfsug/include'),str(src/'nfsug_android_core.c'),str(src/'observer.c'),str(src/'native_span.c')]+[str(src/'camera'/name) for name in cpu]+[str(package/'build/mgba-nfsug/libmgba.a'),'-lws2_32','-lshlwapi','-lole32','-luuid','-lm','-Wl,--gc-sections','-o',str(lib)]
env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
with (out/'compile.log').open('w') as log:subprocess.run(cmd,check=True,env=env,stdout=log,stderr=subprocess.STDOUT)
report=dict(result='BUILT_HOST_ROTATION_LIFETIME_OBSERVATION',diagnostic_only=True,logic_changed=False,parent_host_sha256=sha(parent/'capture-host.dll'),parent_provenance_sha256=sha(parent/'source-provenance.json'),original_header_sha256=sha(parent/'source/camera/live_scene.h'),staged_header_sha256=sha(header),library_sha256=sha(lib),exported_existing_functions=names,compile_command=cmd,factory_sha256=sha(Path(__file__)))
(out/'build-report.json').write_text(json.dumps(report,indent=2));print(report['result'],report['library_sha256'])
