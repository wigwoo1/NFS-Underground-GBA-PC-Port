"""Exercise actual swap observer with unavailable/rejected/mismatched drivers."""
from pathlib import Path
import hashlib,json,os,subprocess
source=Path('Y:/CODEX/NFSUG-Native-PC-Port/work/pc');out=Path('C:/NFSUG-Workspace/NFSUG-pc-swap-observation-tests')
s=(source/'scene_gpu.c').read_text();a=s.index('static void swap_observe(');start=s.index('{',a);depth=0
for end in range(start,len(s)):
 if s[end]=='{':depth+=1
 elif s[end]=='}':
  depth-=1
  if not depth:break
body=s[a:end+1]
prefix=r'''
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdint.h>
#include <assert.h>
#include <stdio.h>
typedef struct {BOOL(WINAPI*swap_interval)(int);int swap_interval_value;int(WINAPI*get_swap_interval)(void);int swap_requested,swap_reported;uint64_t swap_attempts,swap_failures,swap_reads,visible_swaps,hidden_swaps;} NFPCSceneGPU;
static int driver,fail_set,ignore_set;static unsigned setter_calls,getter_calls;
static BOOL WINAPI setter(int desired){setter_calls++;if(fail_set)return FALSE;if(!ignore_set)driver=desired;return TRUE;}
static int WINAPI getter(void){getter_calls++;return driver;}
static NFPCSceneGPU fresh(void){NFPCSceneGPU g={0};g.swap_requested=g.swap_reported=-1;driver=0;fail_set=ignore_set=0;setter_calls=getter_calls=0;return g;}
'''
suffix=r'''
int main(void){
 NFPCSceneGPU g=fresh();swap_observe(&g,0);swap_observe(&g,1);assert(g.swap_requested==1&&!g.swap_attempts&&!g.swap_reads&&g.swap_reported==-1);
 g=fresh();g.swap_interval=setter;swap_observe(&g,0);swap_observe(&g,0);assert(setter_calls==1&&g.swap_reported==-1);swap_observe(&g,1);assert(setter_calls==2&&g.swap_interval_value==1&&!g.swap_failures);
 g=fresh();g.get_swap_interval=getter;swap_observe(&g,0);swap_observe(&g,1);assert(!g.swap_attempts&&g.swap_requested==1&&g.swap_reported==0&&getter_calls==2);
 g=fresh();g.swap_interval=setter;g.get_swap_interval=getter;swap_observe(&g,0);fail_set=1;swap_observe(&g,1);swap_observe(&g,1);assert(g.swap_attempts==3&&g.swap_failures==2&&g.swap_interval_value==0&&g.swap_reported==0);fail_set=0;swap_observe(&g,1);assert(g.swap_attempts==4&&g.swap_failures==2&&g.swap_interval_value==1&&g.swap_reported==1);
 g=fresh();g.swap_interval=setter;g.get_swap_interval=getter;ignore_set=1;swap_observe(&g,1);assert(g.swap_interval_value==1&&g.swap_reported==0&&!g.swap_failures);unsigned reads=getter_calls;swap_observe(&g,1);assert(getter_calls==reads&&setter_calls==1);
 puts("PASS_SWAP_UNAVAILABLE_SETTER_ONLY_GETTER_ONLY_FAILURE_RETRY_MISMATCH_NO_STEADY_REQUERY");return 0;
}
'''
path=out/'swap-policy-branches.c';path.write_text(prefix+body+suffix,encoding='utf-8');exe=out/'swap-policy-branches.exe';env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
for name,command in [('build',['C:/msys64/mingw64/bin/gcc.exe','-std=c11','-O2','-Wall','-Wextra','-Werror',str(path),'-o',str(exe)]),('run',[str(exe)])]:
 r=subprocess.run(command,env=env,capture_output=True,text=True);(out/('policy-'+name+'.log')).write_text(r.stdout+r.stderr,encoding='utf-8');r.check_returncode()
assert 'PASS_SWAP_UNAVAILABLE' in r.stdout
report=dict(result='PASS_ACTUAL_SWAP_OBSERVER_DRIVER_BRANCHES',observer_sha256=hashlib.sha256(body.encode()).hexdigest(),gpu_source_sha256=hashlib.sha256((source/'scene_gpu.c').read_bytes()).hexdigest(),test_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),cases=['no extensions','setter only','getter only','set failure and retry','setter success/readback mismatch','no unnecessary steady-state requery'],physical_driver=False)
(out/'swap-policy-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
