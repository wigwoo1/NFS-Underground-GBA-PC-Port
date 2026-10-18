from pathlib import Path
import os,json,hashlib,shutil,subprocess
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');prior=base/'NFSUG-pc-writer-composition-tests';out=base/'NFSUG-pc-writer-shared-tests';out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
b=json.loads((prior/'recipe-gpu-build-report.json').read_text())
for group in ['source_sha256','staged_sha256']:
 for p,h in b[group].items():assert sha(p)==h,p
assert sha(prior/'recipe-gpu.dll')==b['dll_sha256']
for name in ['recipe-regions.dll','region-build-report.json','sky_composition.inc','writer_band_generated.inc']:shutil.copyfile(prior/name,out/name)
s=(here/'recipe_writer.c').read_text();anchor='unsigned char command[80],material[48],data[];';assert s.count(anchor)==1;s=s.replace(anchor,'unsigned char command[80],material[48];const unsigned char*texture_data,*shade_data,*palette_data;NFRecipeSnapshot*shared_snapshot;void*shared_allocation;unsigned char data[];');s='#include "writer_shared.h"\n'+s
anchor=' if(w->texture_address<';assert s.count(anchor)==1;s=s.replace(anchor,' w->texture_data=w->data;w->shade_data=w->data+w->texture_bytes;w->palette_data=w->shade_data+w->shade_bytes;\n'+anchor)
s=s.replace('void nf_pc_recipe_writer_free(NFPCRecipeWriter*w){free(w);}','void nf_pc_recipe_writer_free(NFPCRecipeWriter*w){if(!w)return;if(w->shared_allocation){nf_recipe_snapshot_free(w->shared_snapshot);nf_pc_writer_ledger_free(w->shared_allocation);}else free(w);}')
s=s.replace('{w->command,w->data,w->data+w->texture_bytes,w->data+w->texture_bytes+w->shade_bytes,w->material}','{w->command,w->texture_data,w->shade_data,w->palette_data,w->material}').replace('w->data[offset]','w->texture_data[offset]').replace('w->data[w->texture_bytes+index*16]','w->shade_data[index*16]');s+='\n#include "writer_shared_decode.inc"\n';writer=out/'writer_shared_generated.c';writer.write_text(s)
s=(here/'writer_address_map.c').read_text().replace('#include "recipe_writer.c"','#include "writer_shared_generated.c"').replace('w->data[offset]','w->texture_data[offset]');address=out/'writer_shared_address_map.c';address.write_text(s)
old=prior/'scene_gpu_writer_composition.c';staged=out/'scene_gpu_writer_shared.c';staged.write_bytes(old.read_bytes())
args=[a.replace(str(old),str(staged)).replace(str(prior/'recipe-gpu.dll'),str(out/'recipe-gpu.dll')) for a in b['command']];oldaddr=[a for a in args if Path(a).name=='writer_address_map.c'];assert len(oldaddr)==1;args=[str(address) if a==oldaddr[0] else a for a in args];args[1:1]=[str(here/'writer_shared_store.c')];env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','');subprocess.run(args,env=env,check=True)
b.update(result='BUILT_SHARED_RAW_WRITER_STORE_TESTS_PENDING',dll_sha256=sha(out/'recipe-gpu.dll'),command=args,script_sha256=sha(Path(__file__)),previous_gpu_sha256=sha(prior/'recipe-gpu.dll'),previous_receipt_sha256=sha(prior/'recipe-gpu-build-report.json'))
for n in ['writer_shared.h','writer_shared_store.c','writer_shared_decode.inc','recipe_store.c','recipe_store.h']:b['source_sha256'][str(here/n)]=sha(here/n)
b['staged_sha256']={str(p):sha(p) for p in [staged,writer,address,out/'sky_composition.inc',out/'writer_band_generated.inc']};(out/'recipe-gpu-build-report.json').write_text(json.dumps(b,indent=2));print('STRICT_SHARED_WRITER_BUILD_PASS',b['dll_sha256'])
