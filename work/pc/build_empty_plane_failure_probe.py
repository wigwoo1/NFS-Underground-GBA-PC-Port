"""Diagnostic-only scene preparation stage tags; preserve original decisions."""
from pathlib import Path
import hashlib,json,os,re,subprocess
source=Path(__file__).resolve().parent;root=source.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-empty-plane-failure-probe';out.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();receipt=base/'NFSUG-pc-empty-model-plane-tests/empty-plane-build-report.json';r=json.loads(receipt.read_text())
for n,h in r['source_sha256'].items():assert sha(source/n)==h,n
for n,h in r.get('reused_camera_source_sha256',{}).items():assert sha(root/'work/camera'/n)==h,n
s=(base/'NFSUG-pc-empty-model-plane-tests/source_scene_empty_plane.c').read_text();mapping={};counter=0
pattern=re.compile(r'goto (fail|owner_done);')
def tag(m):
 global counter
 counter+=1;mapping[str(counter)]=dict(target=m.group(1),source_line=s[:m.start()].count('\n')+1,statement=s.splitlines()[s[:m.start()].count('\n')])
 return '{if(!nf_scene_probe_stage)nf_scene_probe_stage='+str(counter)+';goto '+m.group(1)+';}'
s=pattern.sub(tag,s)
s=s.replace('float*p=c->planes+i*11;','nf_scene_probe_triangle=i;float*p=c->planes+i*11;',1)
a='static size_t cap32(';assert s.count(a)==1;s=s.replace(a,'static uint64_t nf_scene_probe_stage,nf_scene_probe_detail[32],nf_scene_probe_triangle;\nNFPC_API int nf_pc_scene_failure_detail(uint64_t out[32]){if(!out)return 0;memcpy(out,nf_scene_probe_detail,256);return 1;}\n'+a,1)
a='NFPCScene* nf_pc_scene_prepare(const NFPCSourceFrame*frame,size_t maximum){';assert s.count(a)==1;s=s.replace(a,a+'nf_scene_probe_triangle=UINT64_MAX;nf_scene_probe_stage=0;memset(nf_scene_probe_detail,0,sizeof(nf_scene_probe_detail));',1)
a='fail:nf_pc_scene_free(s);return NULL;';assert s.count(a)==1;s=s.replace(a,'fail:nf_scene_probe_detail[0]=nf_scene_probe_stage;nf_scene_probe_detail[9]=nf_scene_probe_triangle;memcpy(nf_scene_probe_detail+1,s->info,64);if(s->info[3])memcpy(nf_scene_probe_detail+16,s->commands[s->info[3]-1].info,128);nf_pc_scene_free(s);return NULL;',1)
staged=out/'source_scene_prepare_failure_probe.c';staged.write_text(s);dll=out/'source-scene-failure.dll'
cmd=[str(staged) if a==str(base/'NFSUG-pc-empty-model-plane-tests/source_scene_empty_plane.c') else str(dll) if a.endswith('source-scene-empty-plane.dll') else a for a in r['command']];assert str(staged) in cmd and str(dll) in cmd;cmd.insert(1,'-I'+str(source));env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
with (out/'build.log').open('w') as log:subprocess.run(cmd,env=env,check=True,stdout=log,stderr=subprocess.STDOUT)
(out/'failure-stages.json').write_text(json.dumps(mapping,indent=2));result=dict(result='BUILT_READONLY_SCENE_PREPARE_STAGE_PROBE',dll_sha256=sha(dll),baseline_dll_sha256=sha(base/'NFSUG-pc-empty-model-plane-tests/source-scene-empty-plane.dll'),baseline_receipt_sha256=sha(receipt),staged_c_sha256=sha(staged),stage_map_sha256=sha(out/'failure-stages.json'),script_sha256=sha(Path(__file__)),source_sha256=r['source_sha256'],decisions_changed=False,full_scene_60fps=False);(out/'scene-prepare-probe-build-report.json').write_text(json.dumps(result,indent=2));print(result['result'],result['dll_sha256'])
