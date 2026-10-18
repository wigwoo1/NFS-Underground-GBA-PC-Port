from pathlib import Path
import os,json,hashlib,shutil,subprocess
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');baseline=base/'NFSUG-pc-recipe-wall-share-tests';out=base/'NFSUG-pc-recipe-runtime-tests';source=out/'source';out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((baseline/'live-recipe-build-report.json').read_text());assert sha(baseline/'capture-host.dll')==r['core_sha256']
for name,h in r['source_sha256'].items():assert sha(baseline/'source'/name)==h
shutil.copytree(baseline/'source',source,dirs_exist_ok=True)
p=source/'live_recipe_capture.inc';s=p.read_text();prefix='static uint64_t pc_profile_calls[3],pc_profile_ticks[3];\nextern void nf_pc_recipe_hash_reset(void);\n';assert s.startswith(prefix);s=s[len(prefix):];a='memset(pc_profile_calls,0,sizeof(pc_profile_calls));memset(pc_profile_ticks,0,sizeof(pc_profile_ticks));nf_pc_recipe_hash_reset();';assert s.count(a)==1;s=s.replace(a,'',1);at=s.index('static void pc_profile_end(');s=s[:at]
for a,b in [('static void pc_profile_road(', 'void nf_pc_road_recipe_capture('),('static void pc_profile_wall(', 'void nf_pc_wall_lineage_event('),('static void pc_profile_close(', 'void nf_pc_live_recipe_owner_close(')]:assert s.count(a)==1;s=s.replace(a,b,1)
p.write_text(s)
p=source/'recipe_store.c';s=p.read_text();start=s.index('static uint64_t pc_hash_calls,pc_hash_bytes,pc_hash_ticks;');end=s.index('static unsigned bucket(',start);s=s[:start]+s[end:];assert s.count('pc_raw_hash(')==1;s=s.replace('pc_raw_hash(','hash(',1);p.write_text(s)
args=[a.replace(str(baseline/'source'),str(source)).replace(str(baseline/'capture-host.dll'),str(out/'capture-host.dll')) for a in r['command']];env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
with (out/'build.log').open('w') as log:subprocess.run(args,env=env,check=True,stdout=log,stderr=subprocess.STDOUT)
strict=['C:/msys64/mingw64/bin/gcc.exe','-O2','-Wall','-Wextra','-Werror','-shared',str(source/'recipe_store.c'),'-o',str(out/'recipe-store-runtime.dll')];subprocess.run(strict,env=env,check=True)
report=dict(result='BUILT_UNINSTRUMENTED_OWNED_RECIPE_CAPTURE',core_sha256=sha(out/'capture-host.dll'),baseline_build_report_sha256=sha(baseline/'live-recipe-build-report.json'),source_sha256={str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file()},script_sha256=sha(Path(__file__)),command=args,strict_store_command=strict,strict_store_dll_sha256=sha(out/'recipe-store-runtime.dll'),profiling_removed=True,shipping_packages_changed=False)
(out/'live-recipe-build-report.json').write_text(json.dumps(report,indent=2));print(report['result'],report['core_sha256'])
