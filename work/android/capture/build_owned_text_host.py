"""Build isolated owned-text extension; legacy capture staging and app stay unchanged."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--event-provenance',action='store_true');p.add_argument('--assembly-diagnostic',action='store_true');p.add_argument('--object-trace',action='store_true');p.add_argument('--wall-span-trace',action='store_true');p.add_argument('--model-outcomes',action='store_true');p.add_argument('--visibility-diagnostic',action='store_true');p.add_argument('--visibility-capacity',type=int,choices=(20,64),default=20);a=p.parse_args();here=Path(__file__).resolve().parent;project=here.parents[2];source=a.output/'source';subprocess.run([sys.executable,str(here/'stage_capture.py'),'--output',str(a.output)],check=True)
extension_hashes={n:hashlib.sha256((here/n).read_bytes()).hexdigest() for n in ('owned_text_observer.inc','owned_text_core.inc','nfsug_owned_text.h')}
for filename,extension in (('observer.c','owned_text_observer.inc'),('nfsug_android_core.c','owned_text_core.inc')):
 with (source/filename).open('a',encoding='utf-8') as f:f.write('\n'+(here/extension).read_text())
if a.model_outcomes:
 extension=here/'owned_model_outcome.inc'
 with (source/'observer.c').open('a',encoding='utf-8') as f:f.write('\n'+extension.read_text())
 extension_hashes[extension.name]=hashlib.sha256(extension.read_bytes()).hexdigest()
if a.visibility_diagnostic:
 header=source/'camera/live_visibility.h';text=header.read_text();start=text.index(' if(pc==0x03004c74&&live_visibility.stage!=1');end=text.index('/* Entire captured scene regenerated',start);body=text[start:end]
 needle='live_visibility.stats[2]++;return;';assert body.count(needle)==7
 chunks=body.split(needle);body=chunks[0]
 for reason,chunk in enumerate(chunks[1:],1):
  # Record before reset so original ownership and phase remain visible.
  reset='live_visibility_reset();'
  if body.endswith(reset):body=body[:-len(reset)];suffix=reset
  else:suffix=''
  call=f'nf_owned_visibility_reject(live_scene_epoch,live_scene.serial,{reason},pc,c->frameCounter(c),live_visibility.state,live_visibility.prepared,live_visibility.stage,live_visibility.query_frame,0,0,0);'
  body+=call+suffix+needle+chunk
 eval_needle='int ok=nf_visibility_snapshot_evaluate(live_visibility.pending,&native)&&'
 assert body.count(eval_needle)==1;body=body.replace(eval_needle,'int evaluation_ok=nf_visibility_snapshot_evaluate(live_visibility.pending,&native);int ok=evaluation_ok&&')
 mismatch='if(!ok||memcmp(&native,&original,sizeof(native))){'
 assert body.count(mismatch)==1
 evidence='uint32_t mismatch=0,first=0;if(ok){mismatch=(memcmp(native.state,original.state,sizeof(native.state))?1:0)|(memcmp(native.queue,original.queue,sizeof(native.queue))?2:0)|(memcmp(native.groups,original.groups,sizeof(native.groups))?4:0)|(native.selected!=original.selected?8:0);for(unsigned k=0;k<sizeof(native);k++)if(((unsigned char*)&native)[k]!=((unsigned char*)&original)[k]){first=k+1;break;}}else {mismatch=0x80000000|(evaluation_ok?0:1);first=nfs_visibility_failure_stage();}'
 # Last rejection is the compare gate; preserve its detailed comparison.
 call='nf_owned_visibility_reject(live_scene_epoch,live_scene.serial,7,pc,c->frameCounter(c),live_visibility.state,live_visibility.prepared,live_visibility.stage,live_visibility.query_frame,0,0,0);'
 assert body.count(call)==1;body=body.replace(mismatch,mismatch+evidence).replace(call,call.replace(',0,0,0);',',mismatch,first,sizeof(native));'))
 fixture='NFVisibilityResult captured_original={0};int original_ok=native_surface_read(NULL,live_visibility.state,captured_original.state,256)&&native_surface_read(NULL,rd32(live_visibility.state+0x60),captured_original.queue,NF_VISIBILITY_QUEUE_BYTES)&&native_surface_read(NULL,rd32(live_visibility.state+0x64),captured_original.groups,4096);captured_original.selected=rd16(0x03005d44);if(original_ok)nf_owned_visibility_fixture(live_scene.serial,live_visibility.state,live_visibility.selected,live_visibility.recovery,live_visibility.base,live_visibility.query,live_visibility.view,live_visibility.ram,sizeof(live_visibility.ram),&captured_original,sizeof(captured_original));'
 body=body.replace(mismatch+evidence,mismatch+evidence+fixture)

 extension=here/'owned_visibility_diagnostic.inc';text=text[:start]+body+text[end:];header.write_text('extern unsigned nfs_visibility_failure_stage(void);\n'+extension.read_text()+'\n'+text);extension_hashes[extension.name]=hashlib.sha256(extension.read_bytes()).hexdigest();extension_hashes['staged_visibility_diagnostic.h']=hashlib.sha256(header.read_bytes()).hexdigest()

if a.wall_span_trace:
 observer=source/'observer.c';text=observer.read_text();needle='static bool onArm(struct ARMCore* cpu){';assert text.count(needle)==1;text=text.replace(needle,'static void nf_owned_wall_span_observe(struct ARMCore*,unsigned);\n'+needle)
 needle='unsigned pc=cpu->gprs[15]-4;';assert text.count(needle)==1;text=text.replace(needle,needle+'nf_owned_wall_span_observe(cpu,pc);')
 extension=here/'owned_wall_span_trace.inc';observer.write_text(text+'\n'+extension.read_text());extension_hashes[extension.name]=hashlib.sha256(extension.read_bytes()).hexdigest();extension_hashes['staged_wall_span_observer.c']=hashlib.sha256(observer.read_bytes()).hexdigest()

if a.object_trace:
 observer=source/'observer.c';text=observer.read_text();needle='static bool onArm(struct ARMCore* cpu){';assert text.count(needle)==1;text=text.replace(needle,'static void nf_owned_original_object_trace(struct ARMCore*,unsigned,unsigned);\n'+needle)
 needle='unsigned pc=cpu->gprs[15]-4;';assert text.count(needle)==1;text=text.replace(needle,needle+'nf_owned_original_object_trace(cpu,pc,cpu->prefetch[0]);')
 extension=here/'owned_object_trace.inc';text+='\n'+extension.read_text();observer.write_text(text);extension_hashes[extension.name]=hashlib.sha256(extension.read_bytes()).hexdigest();extension_hashes['staged_object_trace_observer.c']=hashlib.sha256(observer.read_bytes()).hexdigest()
if a.assembly_diagnostic:
 header=source/'camera/scene_assembly.c';text=header.read_text();start=text.index('static int assembly_commands_impl(');end=text.index('\n}\n',start)+3;body=text[start:end]
 body=body.replace(' NFSceneAssembly*s=nf_assembly_create();',' memset(owned_assembly_diag,0,sizeof(owned_assembly_diag));owned_assembly_diag[0]=1;owned_assembly_diag[11]=count;owned_assembly_diag[9]=serial;NFSceneAssembly*s=nf_assembly_create();')
 body=body.replace('const uint32_t*id=identities+i*5;', 'const uint32_t*id=identities+i*5;owned_assembly_diag[0]=2;owned_assembly_diag[1]=i;owned_assembly_diag[2]=c->kind;owned_assembly_diag[3]=c->source;memcpy(owned_assembly_diag+4,id,20);')
 rules=[('if(kind==3&&model_selector){',10),('else if(assets){ok=',11),('assembly_asset_stats[1]++;ok=',12),('uint8_t*indices=NULL;uint32_t width,height;void*tagged=NULL;',13),('if(ok&&kind==3){ok=',14),('else if(ok){ok=nf_assembly_surface',15),('uint8_t*indices=NULL;uint32_t width,height;\n    ok=',16),('if(ok&&(indexed&8)){NFRoadSourceAttributes raw;',17),('uint8_t*states=NULL;uint32_t width,height,planes;',18)]
 for old,stage in rules:
  assert old in body,old
  if old.endswith('ok='):new=old[:-3]+f'owned_assembly_diag[0]={stage};ok='
  elif old=='if(kind==3&&model_selector){':new=old+f'owned_assembly_diag[0]={stage};'
  elif old=='else if(ok){ok=nf_assembly_surface':new=f'else if(ok){{owned_assembly_diag[0]={stage};ok=nf_assembly_surface'
  else:new=old+f'owned_assembly_diag[0]={stage};'
  body=body.replace(old,new)
 body=body.replace('if(ok)ok=nf_assembly_bounds(', 'if(ok){owned_assembly_diag[0]=19;ok=nf_assembly_bounds(').replace('bounds?bounds+i*4:c->bounds);','bounds?bounds+i*4:c->bounds);}')
 body=body.replace('if(ok)ok=nf_assembly_finish(', 'if(ok){owned_assembly_diag[0]=20;ok=nf_assembly_finish(').replace('131072,out,out_size);','131072,out,out_size);if(ok)owned_assembly_diag[0]=0;}')
 body=body.replace(' nf_assembly_destroy(s);',' owned_assembly_diag[10]=surfaces;nf_assembly_destroy(s);')
 text=text[:start]+body+text[end:];at=text.index('\n')+1;text=text[:at]+'#include <stdint.h>\n#include <string.h>\nstatic uint32_t owned_assembly_diag[12];\n__declspec(dllexport) void nf_owned_assembly_detail(uint32_t out[12]){if(out)memcpy(out,owned_assembly_diag,48); }\n'+text[at:];header.write_text(text)
 extension_hashes['staged_scene_assembly.c']=hashlib.sha256(header.read_bytes()).hexdigest()
if a.event_provenance:
 header=source/'camera/world_trace.h';text=header.read_text();needle='if(ok)ok=nf_scene_submit(native_live_scene,&event,1);';assert text.count(needle)==1
 text=text.replace(needle,needle+'if(ok)nf_owned_event_audit(kind,native_live_scene,&event);')
 needle='static void native_live_frame_close(void){';assert text.count(needle)==1;text=text.replace(needle,needle+'nf_owned_event_audit_close(c->frameCounter(c)+1);')
 text='static void nf_owned_event_audit(unsigned,void*,const void*);static void nf_owned_event_audit_close(unsigned);\n'+text;header.write_text(text)
 compact=here/'owned_compact_wall_history.inc';extension_hashes[compact.name]=hashlib.sha256(compact.read_bytes()).hexdigest()
 with (source/'observer.c').open('a',encoding='utf-8') as f:f.write('\n'+compact.read_text())
 extension=here/'owned_event_provenance.inc';extension_hashes[extension.name]=hashlib.sha256(extension.read_bytes()).hexdigest()
 with (source/'observer.c').open('a',encoding='utf-8') as f:f.write('\n'+extension.read_text())
 extension_hashes['staged_world_trace.h']=hashlib.sha256(header.read_bytes()).hexdigest()
(source/'nfsug_owned_text.h').write_bytes((here/'nfsug_owned_text.h').read_bytes());(source/'nfsug_capture.h').write_bytes((here/'nfsug_capture.h').read_bytes());cpu=json.loads((a.output/'source-provenance.json').read_text())['cpu_sources'];package=project/'work/v2/package/NFSUG-Native-Renderer-source';command=[r'C:\msys64\mingw64\bin\gcc.exe','-O2','-shared','-ffunction-sections','-fdata-sections','-DBUILD_STATIC','-DM_CORE_GBA','-DUSE_DEBUGGERS','-DNF_VISIBILITY_CAPTURE','-DNF_VISIBILITY_QUEUE_CAPACITY='+str(a.visibility_capacity),'-DNF_ROAD_ATTRIBUTE_CORRECTION','-DNF_PACKET_NO_FILES','-D_GNU_SOURCE','-I'+str(source),'-I'+str(source/'camera'),'-I'+str(package/'deps/mgba-0.10.5/include'),'-I'+str(package/'build/mgba-nfsug/include'),str(source/'nfsug_android_core.c'),str(source/'observer.c'),str(source/'native_span.c'),*[str(source/'camera'/n) for n in cpu],str(package/'build/mgba-nfsug/libmgba.a'),'-lws2_32','-lshlwapi','-lole32','-luuid','-lm','-Wl,--gc-sections','-o',str(a.output/'capture-owned-text-host.dll')];env=os.environ.copy();env['PATH']=r'C:\msys64\mingw64\bin;'+env['PATH']
with (a.output/'host-build.log').open('w') as log:subprocess.run(command,env=env,check=True,stdout=log,stderr=subprocess.STDOUT)
report={'result':'PASS_OWNED_TEXT_HOST_BUILD','visibility_capacity':a.visibility_capacity,'library_sha256':hashlib.sha256((a.output/'capture-owned-text-host.dll').read_bytes()).hexdigest(),'extension_sha256':extension_hashes,'staged_only':True,'native_android_build':False,'jni_changed':False};(a.output/'owned-text-build-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

