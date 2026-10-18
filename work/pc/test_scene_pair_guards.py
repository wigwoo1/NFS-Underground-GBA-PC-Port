from pathlib import Path
import ctypes as C,json,hashlib,os,subprocess
root=Path('Y:/CODEX/NFSUG-Native-PC-Port');src=root/'work/pc';out=Path('C:/NFSUG-Workspace/NFSUG-pc-scene-pair-tests');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
fixture=r'''
#include "scene_internal.h"
#include <stdlib.h>
#include <string.h>
NFPC_API NFPCScene* test_scene(unsigned owners,unsigned count){
 if(!owners||owners>2||!count||count>144)return NULL;
 NFPCScene*s=calloc(1,sizeof(*s));if(!s)return NULL;
 s->info[0]=7;s->info[1]=10;s->info[2]=owners;s->info[3]=owners*count;s->info[7]=owners==2?80:0;
 for(unsigned o=0;o<owners;o++){uint64_t k[5]={7,9,7,9,0};memcpy(s->owner[o],k,sizeof(k));
  for(unsigned i=0;i<count;i++){NFPCSceneCommand*c=s->commands+o*count+i;c->info[0]=o;c->info[1]=i==count-1;c->info[2]=i;c->info[3]=c->info[4]=16;c->info[10]=240;c->info[12]=160;c->info[13]=o?80:0;c->info[14]=owners==2&&!o?80:160;c->info[15]=i;c->source_identity[0]=i==count-1?3:1;c->source_identity[1]=1000+i;}}
 return s;
}
NFPC_API void test_advance(NFPCScene*s){s->info[1]++;for(unsigned o=0;o<s->info[2];o++){s->owner[o][1]++;s->owner[o][2]++;s->owner[o][3]++;s->owner[o][4]^=1;}}
NFPC_API void test_info(NFPCScene*s,unsigned f,uint64_t v){s->info[f]=v;}
NFPC_API void test_owner(NFPCScene*s,unsigned o,unsigned f,uint64_t v){s->owner[o][f]=v;}
NFPC_API void test_meta(NFPCScene*s,unsigned i,unsigned f,uint64_t v){s->commands[i].info[f]=v;}
NFPC_API void test_id(NFPCScene*s,unsigned i,unsigned f,uint32_t v){s->commands[i].source_identity[f]=v;}
NFPC_API void test_swap(NFPCScene*s){NFPCSceneCommand t=s->commands[0];s->commands[0]=s->commands[1];s->commands[1]=t;s->commands[0].info[15]=0;s->commands[1].info[15]=1;}
'''
p=out/'scene-pair-fixture.c';p.write_text(fixture);b=json.loads((out/'live-build-report.json').read_text());cmd=list(b['identity_dll_command']);cmd.insert(1,str(p));cmd.insert(1,'-I'+str(src));cmd[cmd.index('-o')+1]=str(out/'scene-pair-fixture.dll');env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
r=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=90);(out/'fixture-build.log').write_text(r.stdout+r.stderr);r.check_returncode()
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(out/'scene-pair-fixture.dll'))
P=C.c_void_p;Q=C.c_uint64;U=C.c_uint32;S=C.c_size_t
def fn(n,args,r=C.c_int):f=getattr(d,n);f.argtypes=args;f.restype=r;return f
make=fn('test_scene',[U,U],P);advance=fn('test_advance',[P],None);iset=fn('test_info',[P,U,Q],None);oset=fn('test_owner',[P,U,U,Q],None);mset=fn('test_meta',[P,U,U,Q],None);idset=fn('test_id',[P,U,U,U],None);swap=fn('test_swap',[P],None);destroy=fn('nf_pc_scene_free',[P],None);prepare=fn('nf_pc_scene_pair_prepare',[P,P,S],P);release=fn('nf_pc_scene_pair_free',[P],None);info=fn('nf_pc_scene_pair_info',[P,P]);row=fn('nf_pc_scene_pair_row',[P,U,P,P]);owner=fn('nf_pc_scene_pair_owner',[P,U,U,P]);cases=[]
def check(label,change=lambda a,b:None,expected=None,reject=False,owners=1,count=3,budget=128*1024):
 a=make(owners,count);b=make(owners,count);advance(b);change(a,b);pair=prepare(a,b,budget)
 try:
  if reject:assert not pair;cases.append(dict(case=label,rejected=True));return
  assert pair;pi=(Q*16)();assert info(pair,pi);old=[];new=[]
  for j in range(pi[5]):
   v=(Q*8)();identity=(U*5)();assert row(pair,j,v,identity)
   if v[1]!=0xffffffff:old.append(v[1])
   if v[2]!=0xffffffff:new.append(v[2])
  assert sorted(old)==list(range(owners*count)) and sorted(new)==list(range(owners*count))
  if expected:
   for field,value in expected.items():assert pi[field]==value,(label,list(pi),expected)
  for endpoint in [2,0xffffffff]:
   v=(Q*5)(*[0x12345678]*5);assert not owner(pair,0,endpoint,v) and list(v)==[0x12345678]*5
  for badindex in [pi[5],0xffffffff]:
   v=(Q*8)(*[0x12345678]*8);ids=(U*5)(*[0x98765432]*5);assert not row(pair,badindex,v,ids) and list(v)==[0x12345678]*8 and list(ids)==[0x98765432]*5
  assert not row(pair,0,None,(U*5)()) and not row(pair,0,(Q*8)(),None) and not info(None,(Q*16)())
  bytes_needed=pi[13];assert not prepare(a,b,bytes_needed-1);exact=prepare(a,b,bytes_needed);assert exact;release(exact)
  snapshot=bytes(pi);destroy(a);a=None;destroy(b);b=None;after=(Q*16)();assert info(pair,after) and bytes(after)==snapshot
  cases.append(dict(case=label,info=list(pi),all_commands_accounted_once=True,scene_destruction_survived=True))
 finally:
  if pair:release(pair)
  if a:destroy(a)
  if b:destroy(b)
check('shared_source_keys',expected={5:3,6:3,7:0,8:0,9:0})
check('source_reorder',lambda a,b:swap(b),{6:3,12:2})
check('metadata_change',lambda a,b:mset(b,0,3,32),{6:3,11:1})
check('enter_and_exit',lambda a,b:idset(b,0,1,9999),{5:4,6:2,7:1,8:1})
check('duplicate_old',lambda a,b:idset(a,1,1,1000),{5:5,6:1,8:1,9:3})
check('duplicate_new',lambda a,b:idset(b,1,1,1000),{5:5,6:1,7:1,9:3})
check('duplicate_both',lambda a,b:(idset(a,1,1,1000),idset(b,1,1,1000)),{5:5,6:1,9:4})
check('held_owner',lambda a,b:[oset(b,0,f,v) for f,v in enumerate([7,9,7,9,0])],{6:0,10:3})
check('two_owners_same_source_ids',expected={5:6,6:6,9:0},owners=2)
check('maximum_commands',expected={5:288,6:288},owners=2,count=144)
for label,change in [('epoch',lambda a,b:iset(b,0,8)),('backward_refresh',lambda a,b:iset(b,1,9)),('equal_refresh',lambda a,b:iset(b,1,10)),('long_gap',lambda a,b:iset(b,1,19)),('owner_count',lambda a,b:iset(b,2,2)),('partition_cut',lambda a,b:iset(b,7,80)),('owner_serial',lambda a,b:oset(b,0,1,9)),('owner_end',lambda a,b:oset(b,0,3,9)),('owner_epoch',lambda a,b:oset(b,0,0,8)),('invalid_page',lambda a,b:oset(b,0,4,2)),('zero_source_kind',lambda a,b:idset(b,0,0,0))]:check(label,change,reject=True)
check('zero_budget',reject=True,budget=0);check('oversized_budget',reject=True,budget=128*1024+1)
assert not prepare(None,None,128*1024)
report=dict(result='PASS_SCENE_PAIR_AMBIGUITY_TEMPORAL_LIFETIME_BUDGET_GUARDS',cases=cases,fixture_sha256=sha(p),fixture_dll_sha256=sha(out/'scene-pair-fixture.dll'),pair_source_sha256=sha(src/'scene_pair.c'),pair_header_sha256=sha(src/'scene_pair.h'),test_sha256=sha(Path(__file__)),full_scene_60fps=False)
(out/'guard-test-report.json').write_text(json.dumps(report,indent=2));print(report['result'],len(cases))
