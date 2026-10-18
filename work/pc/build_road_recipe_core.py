from pathlib import Path
import os,json,hashlib,shutil,subprocess
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');baseline=base/'NFSUG-pc-direct-ram-core-tests';out=base/'NFSUG-pc-road-recipe-tests';source=out/'source';out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
receipt=json.loads((baseline/'owned-core-build-report.json').read_text());assert sha(baseline/'capture-host.dll')==receipt['core_sha256']
for name,digest in receipt['staged_input_sha256'].items():assert sha(baseline/'source'/name)==digest
shutil.copytree(baseline/'source',source,dirs_exist_ok=True)
def replace(text,a,b):
 assert text.count(a)==1,a
 return text.replace(a,b,1)
p=source/'camera/world_trace.h';text=p.read_text()
text=replace(text,'static int (*native_source_event_sink)(uint64_t,unsigned,const NFSceneEvent*);', '''static int (*native_source_event_sink)(uint64_t,unsigned,const NFSceneEvent*);
extern uint64_t nf_pc_road_event_receipt(void);
extern void nf_pc_road_recipe_reset(void);
extern void nf_pc_road_recipe_capture(uint64_t,unsigned,unsigned,unsigned,unsigned,const uint32_t*,unsigned,unsigned,const uint8_t*const*,const unsigned*,const void*,unsigned);
extern int nf_pc_road_scratch_write(const void*,void*,size_t,size_t*);
extern void* nf_pc_road_scratch_read(const void*,size_t);
static uint64_t pc_road_submit_receipt;''')
text=replace(text,'if(ok&&native_source_event_sink)native_source_event_sink(nf_native_scene_epoch(),c->frameCounter(c),&event);',
 'pc_road_submit_receipt=0;if(ok&&native_source_event_sink){int accepted=native_source_event_sink(nf_native_scene_epoch(),c->frameCounter(c),&event);if(accepted&&kind==1)pc_road_submit_receipt=nf_pc_road_event_receipt();}')
text=replace(text,'unsigned runs=0;uint64_t missing=0;', 'unsigned runs=0;uint64_t missing=0,road_receipt=0;uint8_t road_scratch_before[6148];size_t road_scratch_bytes=0;')
needle='native_live_submit(1,out,runs,shift,rd32(material+40),(1u<<shift)*height*2,1);'
text=replace(text,needle,needle+'road_receipt=pc_road_submit_receipt;')
text=replace(text,'nf_geometry_sources_append(1,state,blocks,sizes,12);',
 'nf_geometry_sources_append(1,state,blocks,sizes,12);nf_pc_road_recipe_capture(road_receipt,c->frameCounter(c),state,source,descriptor,out,runs,(unsigned)(mat[36]|((unsigned)mat[37]<<8)),blocks,sizes,road_scratch_before,(unsigned)road_scratch_bytes);')
text=replace(text,'static int native_live_submit(unsigned kind,const uint32_t*commands,unsigned count,unsigned shift,unsigned address,unsigned texture_bytes,int start){','static int native_live_submit(unsigned kind,const uint32_t*commands,unsigned count,unsigned shift,unsigned address,unsigned texture_bytes,int start){pc_road_submit_receipt=0;')
text=replace(text,'if(ok)ok=nf_road_source_runs(native_road_scratch,','if(ok)nf_pc_road_scratch_write(native_road_scratch,road_scratch_before,sizeof(road_scratch_before),&road_scratch_bytes);if(ok)ok=nf_road_source_runs(native_road_scratch,')
p.write_text(text)
p=source/'observer.c';text=p.read_text();text=replace(text,'static void android_wall_clear(void){','static void android_wall_clear(void){nf_pc_road_recipe_reset();');text+='\n#include "road_recipe_capture.inc"\n';p.write_text(text)
p=source/'camera/native_road_source_decode.c'
p.write_text(p.read_text()+'''
__declspec(dllexport) int nf_pc_road_scratch_write(const void*handle,void*out,size_t n,size_t*bytes){
 if(!handle||!out||!bytes)return 0;const RoadScratch*s=handle;if(s->count>512||n<4+(size_t)s->count*12)return 0;uint8_t*b=out;memcpy(b,&s->count,4);for(unsigned i=0;i<s->count;i++){memcpy(b+4+i*12,s->address+i,4);memcpy(b+8+i*12,s->depth+i,8);}*bytes=4+(size_t)s->count*12;return 1;
}
__declspec(dllexport) void* nf_pc_road_scratch_read(const void*data,size_t n){
 if(!data||n<4)return NULL;unsigned count;memcpy(&count,data,4);if(count>512||n!=4+(size_t)count*12)return NULL;RoadScratch*s=calloc(1,sizeof(*s));if(!s)return NULL;s->count=count;const uint8_t*b=data;for(unsigned i=0;i<count;i++){memcpy(s->address+i,b+4+i*12,4);memcpy(s->depth+i,b+8+i*12,8);if(!isfinite(s->depth[i])){free(s);return NULL;}for(unsigned j=0;j<i;j++)if(s->address[j]==s->address[i]){free(s);return NULL;}}return s;
}
''')
shutil.copy2(here/'road_recipe_capture.inc',source/'road_recipe_capture.inc')
args=[arg.replace(str(baseline/'source'),str(source)).replace(str(baseline/'capture-host.dll'),str(out/'capture-host.dll')) for arg in receipt['command']];env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
with (out/'build.log').open('w') as log:subprocess.run(args,env=env,check=True,stdout=log,stderr=subprocess.STDOUT)
r=dict(result='BUILT_ISOLATED_EXPLICIT_ROAD_RECIPE_CAPTURE',core_sha256=sha(out/'capture-host.dll'),baseline_core_sha256=sha(baseline/'capture-host.dll'),source_sha256={str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file()},command=args,script_sha256=sha(Path(__file__)),extension_sha256=sha(here/'road_recipe_capture.inc'),shipping_packages_changed=False)
(out/'recipe-build-report.json').write_text(json.dumps(r,indent=2));print(r['result'],r['core_sha256'])
