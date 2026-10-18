from pathlib import Path
import os,json,hashlib,shutil,subprocess
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');baseline=base/'NFSUG-pc-recipe-alias-tests';out=base/'NFSUG-pc-recipe-wall-share-tests';source=out/'source';out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((baseline/'live-recipe-build-report.json').read_text());assert sha(baseline/'capture-host.dll')==r['core_sha256']
for name,h in r['source_sha256'].items():assert sha(baseline/'source'/name)==h
shutil.copytree(baseline/'source',source,dirs_exist_ok=True)
def replace(t,a,b):assert t.count(a)==1,a;return t.replace(a,b,1)
p=source/'recipe_store.c';text=p.read_text();text+='''
/* Source template owns its common blocks even if its first writer is pruned.
   Only per-column command/shade blocks are rehashed. New key only. */
NFR_API int nf_pc_recipe_store_wall_column(NFRecipeStore*s,uint64_t epoch,uint64_t ordinal,const NFRecipeSnapshot*source,const NFRecipeBlock replacement[2]){
 if(!owner(s)||epoch!=s->epoch||!ordinal||ordinal>INT64_MAX||!source||source->ledger!=s->ledger||source->epoch!=epoch||source->count!=1||source->entries[0].kind!=2||source->entries[0].count!=15||!replacement||find(s,2,ordinal))return 0;
 for(unsigned i=0;i<2;i++)if(!replacement[i].data||!replacement[i].bytes||replacement[i].bytes>0x100000)return 0;
 if(!reserve(s->ledger,sizeof(Writer)))return 0;
 Writer*w=calloc(1,sizeof(*w));if(!w){release(s->ledger,sizeof(Writer));return 0;}
 Blob*staged[2];unsigned staged_count=0;memcpy(w->block,source->entries[0].block,15*sizeof(Blob*));
 /* If a template block lost its live root, prefer an already re-interned
    identical root; otherwise reattach its existing owned allocation at commit. */
 for(unsigned i=0;i<15;i++)if(i!=12&&i!=13&&!w->block[i]->users){Blob*old=w->block[i];for(Blob*b=s->blob[old->hash&(BUCKETS-1)];b;b=b->next)if(b->hash==old->hash&&b->bytes==old->bytes&&!memcmp(b->data,old->data,b->bytes)){w->block[i]=b;break;}}
 for(unsigned i=0;i<2;i++){
  const NFRecipeBlock*v=replacement+i;uint64_t h=hash(v->data,v->bytes);Blob*b=s->blob[h&(BUCKETS-1)];for(;b;b=b->next)if(b->hash==h&&b->bytes==v->bytes&&!memcmp(b->data,v->data,b->bytes))break;
  if(!b)for(unsigned j=0;j<15;j++)if(j!=12&&j!=13&&w->block[j]->hash==h&&w->block[j]->bytes==v->bytes&&!memcmp(w->block[j]->data,v->data,v->bytes)){b=w->block[j];break;}
  if(!b)for(unsigned j=0;j<staged_count;j++)if(staged[j]->hash==h&&staged[j]->bytes==v->bytes&&!memcmp(staged[j]->data,v->data,v->bytes)){b=staged[j];break;}
  if(!b){size_t n=sizeof(Blob)+v->bytes;if(!reserve(s->ledger,n))goto fail;b=malloc(n);if(!b){release(s->ledger,n);goto fail;}b->ledger=s->ledger;InterlockedIncrement(&s->ledger->refs);b->refs=1;b->users=0;b->hash=h;b->bytes=v->bytes;b->next=NULL;memcpy(b->data,v->data,v->bytes);staged[staged_count++]=b;}w->block[12+i]=b;
 }
 w->kind=2;w->ordinal=ordinal;w->count=15;
 for(unsigned i=0;i<15;i++){
  Blob*b=w->block[i];if(!b->users){unsigned at=(unsigned)b->hash&(BUCKETS-1);int present=0;for(Blob*p=s->blob[at];p;p=p->next)if(p==b){present=1;break;}if(!present){unsigned fresh=0;for(unsigned j=0;j<staged_count;j++)fresh|=b==staged[j];if(!fresh)InterlockedIncrement(&b->refs);b->next=s->blob[at];s->blob[at]=b;s->blobs++;}}
  b->users++;InterlockedIncrement(&b->refs);
 }
 unsigned at=bucket(2,ordinal);w->next=s->writer[at];s->writer[at]=w;s->writers++;return 1;
fail:for(unsigned i=0;i<staged_count;i++)blob_drop(staged[i]);release(s->ledger,sizeof(*w));free(w);return 0;
}
''';p.write_text(text)
p=source/'live_recipe_capture.inc';text=p.read_text();text=replace(text,'extern NFRecipeSnapshot*nf_pc_recipe_snapshot_clone(const NFRecipeSnapshot*);','extern NFRecipeSnapshot*nf_pc_recipe_snapshot_clone(const NFRecipeSnapshot*);\nextern int nf_pc_recipe_store_wall_column(NFRecipeStore*,uint64_t,uint64_t,const NFRecipeSnapshot*,const NFRecipeBlock[2]);');text=replace(text,'uint64_t header[8];} PCRecipeWall;','uint64_t header[8];NFRecipeSnapshot*template;} PCRecipeWall;');text=replace(text,'for(unsigned i=0;i<32;i++)free(pc_recipe_wall[i].data);','for(unsigned i=0;i<32;i++){nf_recipe_snapshot_free(pc_recipe_wall[i].template);free(pc_recipe_wall[i].data);}')
text=replace(text,'break;free(w->data);memset(w,0,sizeof(*w));pc_recipe_depth--;','break;nf_recipe_snapshot_free(w->template);free(w->data);memset(w,0,sizeof(*w));pc_recipe_depth--;')
a='if(!nf_recipe_store_put(pc_recipe_pool,epoch,2,ordinal,b,15)){pc_recipe_failed=1;return;}pc_recipe_columns++;'
b='''if(w->template){if(!nf_pc_recipe_store_wall_column(pc_recipe_pool,epoch,ordinal,w->template,b+12)){pc_recipe_failed=1;return;}}else{if(!nf_recipe_store_put(pc_recipe_pool,epoch,2,ordinal,b,15)){pc_recipe_failed=1;return;}uint64_t key[2]={2,ordinal};w->template=nf_recipe_store_snapshot(pc_recipe_pool,epoch,key,1);if(!w->template){pc_recipe_failed=1;return;}}pc_recipe_columns++;'''
text=replace(text,a,b);p.write_text(text)
args=[a.replace(str(baseline/'source'),str(source)).replace(str(baseline/'capture-host.dll'),str(out/'capture-host.dll')) for a in r['command']];env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
with (out/'build.log').open('w') as log:subprocess.run(args,env=env,check=True,stdout=log,stderr=subprocess.STDOUT)
strict=['C:/msys64/mingw64/bin/gcc.exe','-O2','-Wall','-Wextra','-Werror','-shared',str(source/'recipe_store.c'),'-o',str(out/'recipe-store-wall-share.dll')];subprocess.run(strict,env=env,check=True)
report=dict(result='BUILT_OWNED_PER_CALL_WALL_SOURCE_SHARING',core_sha256=sha(out/'capture-host.dll'),baseline_build_report_sha256=sha(baseline/'live-recipe-build-report.json'),source_sha256={str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file()},script_sha256=sha(Path(__file__)),command=args,strict_store_command=strict,strict_store_dll_sha256=sha(out/'recipe-store-wall-share.dll'),shipping_packages_changed=False)
(out/'live-recipe-build-report.json').write_text(json.dumps(report,indent=2));print(report['result'],report['core_sha256'])
