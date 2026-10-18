from pathlib import Path
import json,hashlib,shutil,subprocess,os
BASE=Path('C:/NFSUG-Workspace/')
PARENT=BASE/'NFSUG-pc-owned-retention-ordinals-tests'
OUT=BASE/'NFSUG-pc-scene-retention-ordinals-tests'
ROOT=Path('C:/NFSUG-Workspace/NFSUG-Native-PC-Port')
assert not OUT.exists(), 'Preserve earlier results'
assert shutil.disk_usage(BASE).free>=10*1024**3
OUT.mkdir()
shutil.copytree(PARENT/'build-source',OUT/'build-source')
PC=OUT/'build-source/work/pc'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={n:sha(PC/n) for n in ['source_retention.c','source_retention.h','source_scene.c','source_scene.h']}
for n in before:shutil.copy2(PC/n,OUT/(n+'.before'))
p=PC/'source_retention.c';s=p.read_text()
old='NFPCRetention* nf_pc_source_retention(const NFPCSourceFrame*f,unsigned owner,unsigned kind,size_t maximum)'
assert s.count(old)==1
s=s.replace(old,'static NFPCRetention* source_retention(const NFPCSourceFrame*f,unsigned owner,unsigned kind,size_t maximum,int ordinals)')
target='return nf_pc_retention_decode(h,n,p,pn,o,kind,owner?'
assert s.count(target)==1
s=s.replace(target,'return decode(h,n,p,pn,o,kind,owner?').replace('160:(unsigned)meta[3],maximum);}', '160:(unsigned)meta[3],maximum,ordinals);}')
s+='\nNFPCRetention* nf_pc_source_retention(const NFPCSourceFrame*f,unsigned owner,unsigned kind,size_t maximum){return source_retention(f,owner,kind,maximum,0);}\n'
s+='NFPCRetention* nf_pc_source_retention_ordinals(const NFPCSourceFrame*f,unsigned owner,unsigned kind,size_t maximum){return source_retention(f,owner,kind,maximum,1);}\n'
p.write_text(s)
p=PC/'source_retention.h';s=p.read_text();s=s.replace('#endif','NFPC_API NFPCRetention* nf_pc_source_retention_ordinals(const NFPCSourceFrame*,unsigned owner,unsigned kind,size_t maximum_retained_bytes);\n#endif');p.write_text(s)
p=PC/'source_scene.c';s=p.read_text()
target='nf_pc_source_retention(frame,owner,NFPC_ROAD+layer,maximum-s->info[6])'
assert s.count(target)==1
s=s.replace(target,'(motion==2?nf_pc_source_retention_ordinals:nf_pc_source_retention)(frame,owner,NFPC_ROAD+layer,maximum-s->info[6])')
s+='\nNFPCScene* nf_pc_scene_prepare_motion_ordinals(const NFPCSourceFrame*f,size_t maximum){return prepare_scene(f,maximum,2);}\n'
s+='int nf_pc_scene_retention_ordinals(const NFPCScene*s,unsigned owner,unsigned kind,const uint64_t**p,size_t*n){if(!s||owner>=s->info[2]||(kind!=NFPC_ROAD&&kind!=NFPC_WALL))return 0;return nf_pc_retention_ordinals(s->retained[owner][kind-NFPC_ROAD],p,n);}\n'
p.write_text(s)
p=PC/'source_scene.h';s=p.read_text();s=s.replace('#endif','''/* Explicit opt-in motion scene with owned original history-event ordinal grids.
   Adds307200 bytes per road/wall layer per owner to the SAME total scene budget.
   Original endpoint commands/materials/coverage are preserved. No core/provider
   callback is retained. Does NOT retain history roots/materials or enable motion.
   Existing prepare/prepare_motion behavior and allocation remain unchanged. */
NFPC_API NFPCScene* nf_pc_scene_prepare_motion_ordinals(const NFPCSourceFrame*,size_t);
/* Immutable38400-u64 grid until scene free. Zero outside proof kind/owner rows.
   Invalid/default-scene getters leave outputs unchanged. */
NFPC_API int nf_pc_scene_retention_ordinals(const NFPCScene*,unsigned owner,unsigned kind,const uint64_t**,size_t*);
#endif''');p.write_text(s)
recipe=json.loads((BASE/'NFSUG-pc-scene-sample-tests/live-build-report.json').read_text())
command=[]
for argument in recipe['identity_dll_command']:
    path=Path(argument)
    command.append(str(OUT/'build-source'/path.relative_to(ROOT)) if path.is_absolute() and path.is_relative_to(ROOT) else argument)
command[command.index('-o')+1]=str(OUT/'scene-ordinals.dll')
env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
p=subprocess.run(command,env=env,capture_output=True,text=True,timeout=120)
(OUT/'compile.log').write_text(p.stdout+p.stderr)
assert p.returncode==0,(p.returncode,p.stderr)
report=dict(result='BUILT_SCENE_OWNED_EVENT_ORDINALS',command=command,dll_sha256=sha(OUT/'scene-ordinals.dll'),before_sha256=before,
    changed_sha256={n:sha(PC/n) for n in before},staged_sha256={p.relative_to(OUT).as_posix():sha(p) for p in (OUT/'build-source').rglob('*') if p.is_file()})
(OUT/'build-report.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='staged_sha256'},indent=2),flush=True)
