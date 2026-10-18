from pathlib import Path
import subprocess,os,hashlib
root=Path('Y:/CODEX/NFSUG-Native-PC-Port');out=Path('C:/NFSUG-Workspace/NFSUG-pc-scene-region-tests')
text=(root/'work/pc/test_scene_source_identity.py').read_text().replace("out=base/'NFSUG-pc-scene-source-identity-tests'","out=base/'NFSUG-pc-scene-region-tests'").replace('scene-source-identity.dll','scene-regions.dll')
inject=r'''
from collections import Counter
rp=fn(d,'nf_pc_scene_region_pair_prepare',[P,P,S],P);rf=fn(d,'nf_pc_scene_region_pair_free',[P],None);ri=fn(d,'nf_pc_scene_region_pair_info',[P,P]);rb=fn(d,'nf_pc_scene_region_pair_band',[P,U,P]);rr=fn(d,'nf_pc_scene_region_pair_row',[P,U,P,P]);ro=fn(d,'nf_pc_scene_region_pair_owner',[P,U,U,P]);strict=fn(d,'nf_pc_scene_pair_prepare',[P,P,S],P);strict_free=fn(d,'nf_pc_scene_pair_free',[P],None)
region_counts=Counter();held_region=None;held_region_snapshot=None
def check_region(old,new):
 global held_region,held_region_snapshot
 def scene(s):
  si=(Q*8)();assert sinfo(s,si);commands=[];owners={}
  for i in range(si[3]):
   m=(Q*16)();o=(Q*5)();ids=(U*5)();assert command_info(s,i,m) and identity(s,i,o,ids);commands.append((tuple(m),tuple(o),tuple(ids)));owners[m[0]]=tuple(o)
  return tuple(si),commands,owners
 ai,aa,ao=scene(old);bi,bb,bo=scene(new);pair=rp(old,new,256*1024);assert pair;pi=(Q*16)();assert ri(pair,pi);region_counts['pairs']+=1
 original=strict(old,new,128*1024)
 if original:strict_free(original)
 else:region_counts['previously_rejected_pairs']+=1
 cover=[0]*160;copied_bands=[];copied_rows=[];cursor=0
 for band in range(pi[6]):
  v=(Q*9)();assert rb(pair,band,v);top,bottom,oldrole,newrole,first,count,mode,oldcount,newcount=v
  assert 0<=top<bottom<=160 and first==cursor;cursor+=count
  for y in range(top,bottom):
   cover[y]+=1;assert oldrole==(0 if ai[2]==1 or y<ai[7] else 1) and newrole==(0 if bi[2]==1 or y<bi[7] else 1)
  x,y=ao[oldrole],bo[newrole];expectedmode=1 if x==y else 2 if y[1]>x[1] and 0<y[3]-x[3]<=8 else 3;assert mode==expectedmode
  for ep,key in enumerate([x,y]):
   got=(Q*5)();assert ro(pair,band,ep,got) and tuple(got)==key
  ac=Counter(c[2] for c in aa if c[0][0]==oldrole);bc=Counter(c[2] for c in bb if c[0][0]==newrole);seen_old=[];seen_new=[]
  assert oldcount==sum(ac.values()) and newcount==sum(bc.values());region_counts['bands']+=1;region_counts['mode_'+str(mode)]+=1
  for j in range(first,first+count):
   row=(Q*8)();ids=(U*5)();assert rr(pair,j,row,ids);status,oi,ni,bandindex,flags,oldorder,neworder,kind=row;assert bandindex==band
   a=aa[oi] if oi!=0xffffffff else None;b=bb[ni] if ni!=0xffffffff else None;c=a or b;key=c[2]
   assert tuple(ids)==key and kind==key[0] and bool(flags&4)==(mode==3)
   if a:assert a[0][0]==oldrole;seen_old.append(oi)
   if b:assert b[0][0]==newrole;seen_new.append(ni)
   if ac[key]>1 or bc[key]>1:assert status==4 and not(a and b)
   elif a and b:assert key==b[2] and status=={1:5,2:1,3:6}[mode]
   elif a:assert status==2 and bc[key]==0
   else:assert status==3 and ac[key]==0
   assert oldorder==(a[0][15] if a else 0xffffffff) and neworder==(b[0][15] if b else 0xffffffff)
   region_counts['status_'+str(status)]+=1;copied_rows.append((tuple(row),tuple(ids)))
  assert sorted(seen_old)==[i for i,c in enumerate(aa) if c[0][0]==oldrole] and sorted(seen_new)==[i for i,c in enumerate(bb) if c[0][0]==newrole]
  copied_bands.append(tuple(v))
 assert cover==[1]*160 and cursor==pi[5]
 if held_region:rf(held_region)
 held_region=pair;held_region_snapshot=(tuple(pi),copied_bands,copied_rows)
'''
text=text.replace("rom=root.parent/",inject+"\nrom=root.parent/",1);old='    if held:scene_free(held)';assert text.count(old)==1;text=text.replace(old,'    if held:check_region(held,scene);scene_free(held)')
addition=r'''
assert held_region and region_counts['pairs']==scenes-1 and region_counts['previously_rejected_pairs']==95
pi,bands,rows=held_region_snapshot;after=(Q*16)();assert ri(held_region,after) and tuple(after)==pi
for i,expected in enumerate(bands):v=(Q*9)();assert rb(held_region,i,v) and tuple(v)==expected
for i,expected in enumerate(rows):v=(Q*8)();ids=(U*5)();assert rr(held_region,i,v,ids) and (tuple(v),tuple(ids))==expected
rf(held_region)
(out/'real-region-report.json').write_text(json.dumps(dict(result='PASS_ALL_REAL_SCENE_REGION_TRANSITIONS',counts=dict(region_counts),all160rows_covered_once=True,all_active_commands_accounted_once_per_band=True,scene_source_core_destruction_survived=True,original_frames_and_pcm_exact=True,build_exe_sha256=b['exe_sha256'],core_sha256=b['core_sha256'],dll_sha256=b['identity_dll_sha256'],test_sha256=sha(Path(__file__)),full_scene_60fps=False,motion_enabled=False),indent=2))
print('REGION_COUNTS',dict(region_counts),flush=True)
'''
marker='assert protected=={str(p):sha(p) for p in [rom,state]}';assert text.count(marker)==1;text=text.replace(marker,addition+'\n'+marker)
path=out/('real-region-'+hashlib.sha256(text.encode()).hexdigest()[:12]+'.py');path.write_text(text)
r=subprocess.run([os.sys.executable,str(path)],capture_output=True,text=True,timeout=90);(out/'real-region.log').write_text(r.stdout+r.stderr);print(r.stdout+r.stderr,flush=True);r.check_returncode()
