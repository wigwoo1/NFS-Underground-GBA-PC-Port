from pathlib import Path
import ctypes as C,hashlib,json,os,subprocess
root=Path('Y:/CODEX/NFSUG-Native-PC-Port');src=root/'work/pc';base=Path('C:/NFSUG-Workspace');out=base/'NFSUG-pc-scene-region-tests';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
fixture=(base/'NFSUG-pc-scene-pair-tests/scene-pair-fixture.c').read_text()+r'''
NFPC_API void test_cut(NFPCScene*s,unsigned cut){s->info[7]=cut;for(unsigned i=0;i<s->info[3];i++){unsigned role=(unsigned)s->commands[i].info[0];s->commands[i].info[13]=role?cut:0;s->commands[i].info[14]=s->info[2]==1||role?160:cut;}}
'''
p=out/'scene-region-fixture.c';p.write_text(fixture);b=json.loads((out/'live-build-report.json').read_text());cmd=list(b['identity_dll_command']);cmd.insert(1,str(p));cmd.insert(1,'-I'+str(src));cmd[cmd.index('-o')+1]=str(out/'scene-region-fixture.dll');env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
r=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=90);(out/'fixture-build.log').write_text(r.stdout+r.stderr);r.check_returncode()
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(out/'scene-region-fixture.dll'))
P=C.c_void_p;U=C.c_uint32;Q=C.c_uint64;S=C.c_size_t
def fn(n,args,r=C.c_int):f=getattr(d,n);f.argtypes=args;f.restype=r;return f
make=fn('test_scene',[U,U],P);advance=fn('test_advance',[P],None);cut=fn('test_cut',[P,U],None);iset=fn('test_info',[P,U,Q],None);oset=fn('test_owner',[P,U,U,Q],None);idset=fn('test_id',[P,U,U,U],None);destroy=fn('nf_pc_scene_free',[P],None);prepare=fn('nf_pc_scene_region_pair_prepare',[P,P,S],P);release=fn('nf_pc_scene_region_pair_free',[P],None);info=fn('nf_pc_scene_region_pair_info',[P,P]);band=fn('nf_pc_scene_region_pair_band',[P,U,P]);row=fn('nf_pc_scene_region_pair_row',[P,U,P,P]);owner=fn('nf_pc_scene_region_pair_owner',[P,U,U,P]);cases=[]
def check_pair(a,b,oc,nc,oa,nb,rows=True):
 pair=prepare(a,b,256*1024);assert pair;pi=(Q*16)();assert info(pair,pi);cover=[0]*160;cursor=0;mode_counts={};saved=[]
 for i in range(pi[6]):
  v=(Q*9)();assert band(pair,i,v);top,bottom,oldrole,newrole,first,count,mode,oldcommands,newcommands=v;assert first==cursor;cursor+=count
  mode_counts[mode]=mode_counts.get(mode,0)+1
  for y in range(top,bottom):cover[y]+=1;assert oldrole==(0 if oa==1 or y<oc else 1) and newrole==(0 if nb==1 or y<nc else 1)
  if rows:
   olds=[];news=[]
   for j in range(first,first+count):
    r=(Q*8)();ids=(U*5)();assert row(pair,j,r,ids) and r[3]==i and bool(r[4]&4)==(mode==3)
    if r[1]!=0xffffffff:olds.append(r[1])
    if r[2]!=0xffffffff:news.append(r[2])
   assert len(olds)==oldcommands and len(set(olds))==oldcommands and len(news)==newcommands and len(set(news))==newcommands
  saved.append(tuple(v))
 assert cover==[1]*160 and cursor==pi[5]
 return pair,pi,mode_counts,saved
for ca in range(161):
 for cb in range(161):
  a=make(2,3);b=make(2,3);advance(b);cut(a,ca);cut(b,cb);pair,pi,modes,_=check_pair(a,b,ca,cb,2,2,False);assert modes=={2:pi[6]};release(pair);destroy(a);destroy(b)
cases.append(dict(case='all_split_cut_combinations',pairs=161*161,all160rows_covered_once=True))
for label,oa,nb,ca,cb in [('full_to_split',1,2,0,80),('split_to_full',2,1,80,0),('two_distinct_cuts',2,2,40,120),('maximum_commands',2,2,40,120)]:
 count=144 if label=='maximum_commands' else 3;a=make(oa,count);b=make(nb,count);advance(b);cut(a,ca);cut(b,cb);pair,pi,modes,saved=check_pair(a,b,ca,cb,oa,nb)
 for bad in [pi[6],0xffffffff]:
  v=(Q*9)(*[0xa5a5]*9);assert not band(pair,bad,v) and list(v)==[0xa5a5]*9
 v=(Q*5)(*[0xb6b6]*5);assert not owner(pair,0,2,v) and list(v)==[0xb6b6]*5
 r=(Q*8)(*[0xc7c7]*8);ids=(U*5)(*[0xd8d8]*5);assert not row(pair,pi[5],r,ids) and list(r)==[0xc7c7]*8 and list(ids)==[0xd8d8]*5
 assert not prepare(a,b,pi[13]-1);exact=prepare(a,b,pi[13]);assert exact;release(exact)
 destroy(a);destroy(b)
 for i,e in enumerate(saved):v=(Q*9)();assert band(pair,i,v) and tuple(v)==e
 cases.append(dict(case=label,info=list(pi),scene_destruction_survived=True));release(pair)
# A completed newer owner changes from bottom role1 to sole role0.
a=make(2,3);b=make(1,3);advance(b);cut(a,80)
for f,v in enumerate([7,10,8,10,1]):oset(a,1,f,v);oset(b,0,f,v)
pair,pi,modes,_=check_pair(a,b,80,0,2,1);assert modes=={2:1,1:1} and pi[7]==pi[8]==3;cases.append(dict(case='source_owner_role_handoff',info=list(pi)));release(pair);destroy(a);destroy(b)
# Middle band exposes an older source: represented, explicitly non-interpolable.
a=make(2,3);b=make(2,3);advance(b);cut(a,40);cut(b,120)
for s in [a,b]:
 for role,key in enumerate([[7,9,7,9,0],[7,10,8,10,1]]):
  for f,v in enumerate(key):oset(s,role,f,v)
pair,pi,modes,_=check_pair(a,b,40,120,2,2);assert modes=={1:2,3:1} and pi[12]==3;cases.append(dict(case='backward_source_band_explicit',info=list(pi)));release(pair);destroy(a);destroy(b)
a=make(1,3);b=make(2,3);advance(b);cut(b,80);idset(a,1,1,1000);pair,pi,modes,_=check_pair(a,b,0,80,1,2);assert pi[11]==6;cases.append(dict(case='duplicate_per_band_not_chosen',info=list(pi)));release(pair);destroy(a);destroy(b)
for label,change in [('epoch',lambda a,b:iset(b,0,8)),('same_refresh',lambda a,b:iset(b,1,10)),('backward_refresh',lambda a,b:iset(b,1,9)),('long_scene_gap',lambda a,b:iset(b,1,19)),('bad_cut',lambda a,b:iset(b,7,161)),('zero_owners',lambda a,b:iset(b,2,0)),('owner_epoch',lambda a,b:oset(b,0,0,8)),('bad_owner_page',lambda a,b:oset(b,0,4,2)),('zero_identity',lambda a,b:idset(b,0,0,0))]:
 a=make(1,3);b=make(1,3);advance(b);change(a,b);assert not prepare(a,b,256*1024);destroy(a);destroy(b);cases.append(dict(case=label,rejected=True))
a=make(1,3);b=make(1,3);advance(b);assert not prepare(a,b,0) and not prepare(a,b,256*1024+1);destroy(a);destroy(b);assert not prepare(None,None,256*1024)
report=dict(result='PASS_REGION_COVERAGE_HANDOFF_DISCONTINUITY_AND_GUARDS',cases=cases,cut_sweep_pairs=25921,pair_source_sha256=sha(src/'scene_region_pair.c'),pair_header_sha256=sha(src/'scene_region_pair.h'),fixture_source_sha256=sha(p),fixture_dll_sha256=sha(out/'scene-region-fixture.dll'),test_sha256=sha(Path(__file__)),full_scene_60fps=False)
(out/'guard-report.json').write_text(json.dumps(report,indent=2));print(report['result'],len(cases),25921)
