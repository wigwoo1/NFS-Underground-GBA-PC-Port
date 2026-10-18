from pathlib import Path
import json,hashlib,shutil,subprocess,os,sys
base=Path('C:/NFSUG-Workspace');parent=base/'NFSUG-pc-owned-pose-timing-tests';out=base/'NFSUG-pc-history-source-provenance-tests';source=out/'source';local=Path(__file__).parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
verify='--verify-stage' in sys.argv
if verify:source=out/'recipe-check-source'
assert shutil.disk_usage('C:/').free>10*1024**3;out.mkdir(exist_ok=True);assert not source.exists(),'Preserve immutable diagnostic stage; use compile-only after setup'
build=json.loads((parent/'core-wrapper-build-report.json').read_text());assert sha(parent/'timing-core.dll')==build['core_sha256']
for name,h in build['staged_sha256'].items():
 p=parent/'core-source'/name;assert sha(p)==h;dest=source/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
# Declaration before live_scene.h; definition after both source scene and visibility types.
p=source/'observer.c';text=p.read_text();marker='#include "camera/live_scene.h"';assert text.count(marker)==1;text=text.replace(marker,'static void nf_pc_history_surface_note(const uint32_t[5],const void*,size_t);\n'+marker)
marker='static int android_wall_event(uint64_t epoch,unsigned refresh,const NFSceneEvent*event){';assert text.count(marker)==1;text=text.replace(marker,'#include "history_source_provenance_probe.inc"\n'+marker)
marker=' if(event->kind==1){for(unsigned i=0;i<event->count;i++)';assert text.count(marker)==1;text=text.replace(marker,' if(event->kind==2)nf_pc_history_event_note(epoch,refresh,event,android_wall_ordinal);\n'+marker)
marker='if(!nf_road_history_append(android_road_store,epoch,++android_road_ordinal,refresh,&run)){android_wall_failed=1;return 0;}}}return 1;';assert text.count(marker)==1;text=text.replace(marker,'if(!nf_road_history_append(android_road_store,epoch,++android_road_ordinal,refresh,&run)){android_wall_failed=1;return 0;}nf_pc_history_event_note(epoch,refresh,&run,android_road_ordinal);}}return 1;')
marker='android_wall_owners[1].road_bytes=road_bytes;';assert text.count(marker)==1;text=text.replace(marker,marker+'nf_pc_history_owner_publish(epoch,packet,copy+bytes);');p.write_text(text)
p=source/'camera/live_scene.h';text=p.read_text();marker='nf_surface_free(surface);return;';assert text.count(marker)==1;text=text.replace(marker,'nf_pc_history_surface_note(id,surface,size);'+marker)
marker='nf_surface_free(surface);nf_surface_free(light);';assert text.count(marker)==1;text=text.replace(marker,'nf_pc_history_surface_note(id,surface,size);'+marker);p.write_text(text)
shutil.copyfile(local/'history_source_provenance_probe.inc',source/'history_source_provenance_probe.inc')
for kind,prefix in [('road','RH'),('wall','WH')]:
 p=source/('camera/'+kind+'_history_store.c');text=p.read_text();text+='''
/* Diagnostic original-cell event provenance; no history state changes. */
__declspec(dllexport) size_t nf_'''+kind+'''_history_cell_ordinals(void*handle,uint64_t epoch,unsigned page,void*out,size_t capacity){
 '''+prefix+'''Store*s=handle;size_t bytes=38400u*sizeof(uint64_t);if(!s||s->epoch!=epoch||page>1||(out&&capacity<bytes))return 0;
 if(out){uint64_t*values=out;for(unsigned i=0;i<38400;i++){int slot=s->cells[page*38400+i];values[i]=slot>=0?s->event[slot].ordinal:0;}}return bytes;
}
''';p.write_text(text)
if verify:
 expected=json.loads((out/'history-build-report.json').read_text())['staged_sha256'];actual={str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file()};assert actual==expected,[(k,actual.get(k),v) for k,v in expected.items() if actual.get(k)!=v]
 (out/'recipe-verification.json').write_text(json.dumps(dict(result='PASS_RECIPE_RECREATES_EXACT_TESTED_SOURCE',staged_files=len(actual),builder_sha256=sha(Path(__file__))),indent=2));print('PASS_RECIPE_RECREATES_EXACT_TESTED_SOURCE',len(actual),flush=True);sys.exit(0)
cmd=[x.replace(str(parent/'core-source'),str(source)).replace(str(parent/'timing-core.dll'),str(out/'capture-host.dll')) for x in build['command']]
(out/'command.json').write_text(json.dumps(cmd,indent=2));env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;'+env['PATH'];r=subprocess.run(cmd,capture_output=True,text=True,env=env);(out/'build.log').write_text(r.stdout+r.stderr);print('compile',r.returncode,r.stdout[-1000:]+r.stderr[-1500:],flush=True);r.check_returncode()
report=dict(result='BUILT_READONLY_HISTORY_SOURCE_PROVENANCE_TESTS_PENDING',core_sha256=sha(out/'capture-host.dll'),parent_core_sha256=build['core_sha256'],parent_receipt_sha256=sha(parent/'core-wrapper-build-report.json'),command=cmd,staged_sha256={str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file()},new_game_hooks=False,game_memory_writes=False,shipping_changed=False)
(out/'history-build-report.json').write_text(json.dumps(report,indent=2));print(report['result'],report['core_sha256'],flush=True)
