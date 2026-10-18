from pathlib import Path
import os,json,hashlib,shutil,subprocess
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');baseline=base/'NFSUG-pc-direct-ram-core-tests';out=base/'NFSUG-pc-visibility-pair-tests';source=out/'source';out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
receipt=json.loads((baseline/'owned-core-build-report.json').read_text());assert sha(baseline/'capture-host.dll')==receipt['core_sha256']
for name,digest in receipt['staged_input_sha256'].items():assert sha(baseline/'source'/name)==digest
shutil.copytree(baseline/'source',source,dirs_exist_ok=True);p=source/'observer.c';text=p.read_text(encoding='utf-8');text+='''
/* Diagnostic bridge to EXISTING owned-snapshot visibility regeneration. */
__declspec(dllexport) int nf_pc_visibility_pair(const uint64_t a[5],const uint64_t b[5],double alpha,void**out,size_t*bytes,unsigned*stage){
 if(stage)*stage=30;if(!a||!b||!out||!bytes||!a[0]||a[0]!=b[0])return 0;NFVisibilityIdentity ids[2];const uint64_t*keys[2]={a,b};
 for(unsigned side=0;side<2;side++){unsigned found=0;for(unsigned i=0;i<NF_COMPLETED_SURFACE_HISTORY;i++){NFCompletedSurfaceAudit*e=completed_surface_audit[i];const uint64_t*k=keys[side];if(e&&e->id.epoch==k[0]&&e->id.serial==k[1]&&e->id.begin_refresh==k[2]&&e->id.end_refresh==k[3]&&e->page==k[4]){ids[side]=e->id;found=1;break;}}if(!found){if(stage)*stage=31;return 0;}}
 return nf_live_completed_native_multimodel_world_classified_pair_packet(ids,ids+1,alpha,out,bytes,stage);
}
__declspec(dllexport) void nf_pc_pair_missing_model(uint32_t out[6]){nf_live_paired_model_inputs_missing(out);}
''';p.write_text(text,encoding='utf-8')
args=[arg.replace(str(baseline/'source'),str(source)).replace(str(baseline/'capture-host.dll'),str(out/'capture-host.dll')) for arg in receipt['command']];env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
with (out/'build.log').open('w') as log:subprocess.run(args,env=env,check=True,stdout=log,stderr=subprocess.STDOUT)
r=dict(result='BUILT_EXISTING_VISIBILITY_PAIR_DIAGNOSTIC_BRIDGE',core_sha256=sha(out/'capture-host.dll'),baseline_core_sha256=sha(baseline/'capture-host.dll'),source_sha256={str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file()},command=args,script_sha256=sha(Path(__file__)),existing_pair_implementation_changed=False,shipping_packages_changed=False)
(out/'pair-build-report.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k not in ['source_sha256','command']},indent=2))
