from pathlib import Path
import os,json,hashlib,shutil,subprocess
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');baseline=base/'NFSUG-pc-direct-ram-core-tests';out=base/'NFSUG-pc-wall-lineage-tests';source=out/'source';out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((baseline/'owned-core-build-report.json').read_text());assert sha(baseline/'capture-host.dll')==r['core_sha256']
for name,digest in r['staged_input_sha256'].items():assert sha(baseline/'source'/name)==digest
shutil.copytree(baseline/'source',source,dirs_exist_ok=True)
def replace(t,a,b):assert t.count(a)==1,a;return t.replace(a,b,1)
p=source/'camera/world_trace.h';text=p.read_text();needle='static int (*native_source_event_sink)(uint64_t,unsigned,const NFSceneEvent*);';text=replace(text,needle,needle+'''
extern void nf_pc_wall_lineage_reset(void);
extern void nf_pc_wall_lineage_tick(struct ARMCore*,unsigned);
extern void nf_pc_wall_lineage_recipe(unsigned,const uint8_t*const*,const unsigned*);
extern void nf_pc_wall_lineage_event(uint64_t,unsigned,uint64_t,const NFSceneEvent*);
''');text=replace(text,'static void world_trace(struct ARMCore*cpu,unsigned pc){','static void world_trace(struct ARMCore*cpu,unsigned pc){nf_pc_wall_lineage_tick(cpu,pc);');text=replace(text,'nf_geometry_sources_append(2,state,blocks,sizes,12);','nf_geometry_sources_append(2,state,blocks,sizes,12);nf_pc_wall_lineage_recipe(state,blocks,sizes);');p.write_text(text)
p=source/'observer.c';text=p.read_text();text=replace(text,'static void android_wall_clear(void){','static void android_wall_clear(void){nf_pc_wall_lineage_reset();');needle='if(event->kind==1){for(unsigned i=0;i<event->count;i++){NFSceneEvent run=*event;';text=replace(text,needle,'if(event->kind==2)nf_pc_wall_lineage_event(epoch,refresh,android_wall_ordinal,event);'+needle);text+='\n#include "wall_lineage_capture.inc"\n';p.write_text(text)
shutil.copy2(here/'wall_lineage_capture.inc',source/'wall_lineage_capture.inc');args=[a.replace(str(baseline/'source'),str(source)).replace(str(baseline/'capture-host.dll'),str(out/'capture-host.dll')) for a in r['command']];env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
with (out/'build.log').open('w') as log:subprocess.run(args,env=env,check=True,stdout=log,stderr=subprocess.STDOUT)
report=dict(result='BUILT_ISOLATED_WALL_CALL_LINEAGE_CAPTURE',core_sha256=sha(out/'capture-host.dll'),baseline_core_sha256=sha(baseline/'capture-host.dll'),source_sha256={str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file()},command=args,script_sha256=sha(Path(__file__)),extension_sha256=sha(here/'wall_lineage_capture.inc'),shipping_packages_changed=False)
(out/'lineage-build-report.json').write_text(json.dumps(report,indent=2));print(report['result'],report['core_sha256'])
