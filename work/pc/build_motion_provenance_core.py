"""Expose existing original-operation diagnostics in an isolated core only."""
from pathlib import Path
import os,json,hashlib,shutil,subprocess
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');baseline=base/'NFSUG-pc-direct-ram-core-tests';out=base/'NFSUG-pc-motion-provenance-tests';source=out/'source';out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
receipt=json.loads((baseline/'owned-core-build-report.json').read_text());assert sha(baseline/'capture-host.dll')==receipt['core_sha256']
for name,digest in receipt['staged_input_sha256'].items():assert sha(baseline/'source'/name)==digest
shutil.copytree(baseline/'source',source,dirs_exist_ok=True);p=source/'camera/live_visibility.h';text=p.read_text(encoding='utf-8')
for name in ['int nf_live_completed_operation_order(', 'void nf_live_operation_order_detail(']:
 assert text.count('API '+name)==1;text=text.replace('API '+name,'__declspec(dllexport) '+name,1)
p.write_text(text,encoding='utf-8')
observer=source/'observer.c';text=observer.read_text(encoding='utf-8');text+='''
/* Diagnostic original command ownership, never screen-polygon association. */
__declspec(dllexport) int nf_pc_original_command_provenance(uint64_t epoch,unsigned serial,unsigned pass,uint32_t*out,unsigned capacity,unsigned*count){
 if(!out||!count||capacity>144)return 0;NFNativeSceneCommand*commands=malloc(144*sizeof(*commands));if(!commands)return 0;unsigned n=0;int ok=nf_live_completed_draw_root_commands(epoch,serial,pass,commands,144,&n)&&n<=capacity;
 if(ok){for(unsigned i=0;i<n;i++){NFNativeSceneCommand*c=commands+i;uint32_t*r=out+i*22;r[0]=c->kind;r[1]=c->owner;r[2]=c->pass;r[3]=c->mask;r[4]=c->object;r[5]=c->source;memcpy(r+6,c->xyz,12);memcpy(r+9,c->material,16);memcpy(r+13,c->record,16);for(unsigned j=0;j<4;j++)r[17+j]=c->bounds[j];r[21]=c->cell_end;}*count=n;}
 free(commands);return ok;
}
''';observer.write_text(text,encoding='utf-8')
args=[arg.replace(str(baseline/'source'),str(source)).replace(str(baseline/'capture-host.dll'),str(out/'capture-host.dll')) for arg in receipt['command']];env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
with (out/'build.log').open('w') as log:subprocess.run(args,env=env,check=True,stdout=log,stderr=subprocess.STDOUT)
r=dict(result='BUILT_ORIGINAL_OPERATION_PROVENANCE_DIAGNOSTIC',core_sha256=sha(out/'capture-host.dll'),baseline_core_sha256=sha(baseline/'capture-host.dll'),source_sha256={str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file()},command=args,script_sha256=sha(Path(__file__)),diagnostic_changes=['Export two existing operation-order getters in camera/live_visibility.h','Add original NFNativeSceneCommand ownership-field diagnostic getter to observer.c'],shipping_packages_changed=False)
(out/'provenance-build-report.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k not in ['source_sha256','command']},indent=2))
