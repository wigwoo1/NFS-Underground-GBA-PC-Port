from pathlib import Path
import os,json,hashlib,shutil,subprocess
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');baseline=base/'NFSUG-pc-recipe-profile-tests';out=base/'NFSUG-pc-recipe-alias-tests';source=out/'source';out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((baseline/'live-recipe-build-report.json').read_text());assert sha(baseline/'capture-host.dll')==r['core_sha256']
for name,h in r['source_sha256'].items():assert sha(baseline/'source'/name)==h
shutil.copytree(baseline/'source',source,dirs_exist_ok=True)
p=source/'recipe_store.c';text=p.read_text();text+='''
/* Same successful source batch, distinct immutable original writer key.
   Does not hash/copy source blocks again. All allocation/refcount rules match put. */
NFR_API int nf_pc_recipe_store_alias(NFRecipeStore*s,uint64_t epoch,unsigned kind,uint64_t ordinal,uint64_t source_ordinal){
 if(!owner(s)||epoch!=s->epoch||(kind!=1&&kind!=2)||!ordinal||ordinal>INT64_MAX)return 0;
 Writer*source=find(s,kind,source_ordinal);if(!source)return 0;
 Writer*prior=find(s,kind,ordinal);
 if(prior){if(prior->count!=source->count)return 0;for(unsigned i=0;i<prior->count;i++)if(prior->block[i]!=source->block[i])return 0;return 1;}
 if(!reserve(s->ledger,sizeof(Writer)))return 0;
 Writer*w=calloc(1,sizeof(*w));if(!w){release(s->ledger,sizeof(Writer));return 0;}
 w->kind=kind;w->ordinal=ordinal;w->count=source->count;
 for(unsigned i=0;i<w->count;i++){w->block[i]=source->block[i];w->block[i]->users++;InterlockedIncrement(&w->block[i]->refs);}
 unsigned at=bucket(kind,ordinal);w->next=s->writer[at];s->writer[at]=w;s->writers++;return 1;
}
''';p.write_text(text)
p=source/'live_recipe_capture.inc';text=p.read_text();needle='#include "live_recipe_api.h"';assert text.count(needle)==1;text=text.replace(needle,needle+'\nextern int nf_pc_recipe_store_alias(NFRecipeStore*,uint64_t,unsigned,uint64_t,uint64_t);',1)
a='if(!nf_recipe_store_put(pc_recipe_pool,android_wall_epoch,1,last-count+1+i,b,15))';b='if(!(i?nf_pc_recipe_store_alias(pc_recipe_pool,android_wall_epoch,1,last-count+1+i,last-count+1):nf_recipe_store_put(pc_recipe_pool,android_wall_epoch,1,last-count+1,b,15)))';assert text.count(a)==1;text=text.replace(a,b,1);p.write_text(text)
args=[a.replace(str(baseline/'source'),str(source)).replace(str(baseline/'capture-host.dll'),str(out/'capture-host.dll')) for a in r['command']];env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
with (out/'build.log').open('w') as log:subprocess.run(args,env=env,check=True,stdout=log,stderr=subprocess.STDOUT)
# Strict standalone store variant compilation, independent of legacy core warnings.
strict=['C:/msys64/mingw64/bin/gcc.exe','-O2','-Wall','-Wextra','-Werror','-shared',str(source/'recipe_store.c'),'-o',str(out/'recipe-store-alias.dll')];subprocess.run(strict,env=env,check=True)
report=dict(result='BUILT_IMMUTABLE_SAME_BATCH_ROAD_WRITER_ALIAS',core_sha256=sha(out/'capture-host.dll'),baseline_build_report_sha256=sha(baseline/'live-recipe-build-report.json'),source_sha256={str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file()},script_sha256=sha(Path(__file__)),command=args,strict_store_command=strict,strict_store_dll_sha256=sha(out/'recipe-store-alias.dll'),shipping_packages_changed=False)
(out/'live-recipe-build-report.json').write_text(json.dumps(report,indent=2));print(report['result'],report['core_sha256'])
