from pathlib import Path
import os,json,hashlib,shutil,subprocess
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');road=base/'NFSUG-pc-road-recipe-tests';wall=base/'NFSUG-pc-wall-lineage-tests';out=base/'NFSUG-pc-live-recipe-tests';source=out/'source';out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((road/'recipe-build-report.json').read_text());w=json.loads((wall/'lineage-build-report.json').read_text());store=json.loads((base/'NFSUG-pc-recipe-store-tests/store-build-report.json').read_text())
for folder,receipt in [(road,r),(wall,w)]:
 assert sha(folder/'capture-host.dll')==receipt['core_sha256']
 for name,digest in receipt['source_sha256'].items():assert sha(folder/'source'/name)==digest
for name,digest in store['source_sha256'].items():assert sha(here/name)==digest
shutil.copytree(road/'source',source,dirs_exist_ok=True)
def replace(t,a,b):assert t.count(a)==1,a;return t.replace(a,b,1)
p=source/'camera/world_trace.h';text=p.read_text();needle='static int (*native_source_event_sink)(uint64_t,unsigned,const NFSceneEvent*);';text=replace(text,needle,needle+'''
extern void nf_pc_wall_lineage_tick(struct ARMCore*,unsigned);
extern void nf_pc_wall_lineage_recipe(unsigned,const uint8_t*const*,const unsigned*);
extern void nf_pc_wall_lineage_event(uint64_t,unsigned,uint64_t,const NFSceneEvent*);
''');text=replace(text,'static void world_trace(struct ARMCore*cpu,unsigned pc){','static void world_trace(struct ARMCore*cpu,unsigned pc){nf_pc_wall_lineage_tick(cpu,pc);');text=replace(text,'nf_geometry_sources_append(2,state,blocks,sizes,12);','nf_geometry_sources_append(2,state,blocks,sizes,12);nf_pc_wall_lineage_recipe(state,blocks,sizes);');p.write_text(text)
p=source/'observer.c';text=p.read_text();needle='if(event->kind==1){for(unsigned i=0;i<event->count;i++){NFSceneEvent run=*event;';text=replace(text,needle,'if(event->kind==2)nf_pc_wall_lineage_event(epoch,refresh,android_wall_ordinal,event);'+needle);needle='static void android_wall_close_owner(uint64_t epoch,const NFScenePacket*packet){';text=replace(text,needle,'extern void nf_pc_live_recipe_owner_close(uint64_t,const NFScenePacket*,const void*,size_t,const void*,size_t);\n'+needle);needle=' free(android_wall_owners[0].data);android_wall_owners[0]=android_wall_owners[1];';text=replace(text,needle,' nf_pc_live_recipe_owner_close(epoch,packet,copy+bytes+192080,road_bytes,copy,bytes);\n'+needle);text=replace(text,'#include "road_recipe_capture.inc"','#include "live_recipe_capture.inc"');p.write_text(text)
for name in ['recipe_store.c','recipe_store.h','live_recipe_api.h','live_recipe_capture.inc']:shutil.copy2(here/name,source/name)
p=source/'recipe_store.c';text=p.read_text();text+='''
/* Core owner acquires a separate immutable snapshot before publication. */
NFR_API NFRecipeSnapshot*nf_pc_recipe_snapshot_clone(const NFRecipeSnapshot*source){
 if(!source||!reserve(source->ledger,source->bytes))return NULL;
 NFRecipeSnapshot*p=malloc(source->bytes);if(!p){release(source->ledger,source->bytes);return NULL;}memcpy(p,source,source->bytes);InterlockedIncrement(&p->ledger->refs);for(size_t i=0;i<p->count;i++)for(unsigned j=0;j<p->entries[i].count;j++)InterlockedIncrement(&p->entries[i].block[j]->refs);return p;
}
''';p.write_text(text)
args=[a.replace(str(road/'source'),str(source)).replace(str(road/'capture-host.dll'),str(out/'capture-host.dll')) for a in r['command']];args.insert(args.index('-o'),str(source/'recipe_store.c'));env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
with (out/'build.log').open('w') as log:subprocess.run(args,env=env,check=True,stdout=log,stderr=subprocess.STDOUT)
report=dict(result='BUILT_DIRECT_CAPTURE_OWNED_RECIPE_ADAPTER',core_sha256=sha(out/'capture-host.dll'),road_build_report_sha256=sha(road/'recipe-build-report.json'),wall_build_report_sha256=sha(wall/'lineage-build-report.json'),store_build_report_sha256=sha(base/'NFSUG-pc-recipe-store-tests/store-build-report.json'),source_sha256={str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file()},extension_sha256={name:sha(here/name) for name in ['live_recipe_api.h','live_recipe_capture.inc']},script_sha256=sha(Path(__file__)),command=args,shipping_packages_changed=False)
(out/'live-recipe-build-report.json').write_text(json.dumps(report,indent=2));print(report['result'],report['core_sha256'])
