from pathlib import Path
import subprocess,os,hashlib
root=Path('Y:/CODEX/NFSUG-Native-PC-Port');out=Path('C:/NFSUG-Workspace/NFSUG-pc-scene-pair-tests')
text=(root/'work/pc/test_scene_source_identity.py').read_text().replace("out=base/'NFSUG-pc-scene-source-identity-tests'","out=base/'NFSUG-pc-scene-pair-tests'").replace('scene-source-identity.dll','scene-pair.dll')
inject=r'''
from collections import Counter
pair_prepare=fn(d,'nf_pc_scene_pair_prepare',[P,P,S],P);pair_free=fn(d,'nf_pc_scene_pair_free',[P],None);pair_info=fn(d,'nf_pc_scene_pair_info',[P,P]);pair_row=fn(d,'nf_pc_scene_pair_row',[P,U,P,P]);pair_owner=fn(d,'nf_pc_scene_pair_owner',[P,U,U,P])
pair_counts=Counter();held_pair=None;held_pair_rows=None
def check_pair(old,new):
 global held_pair,held_pair_rows
 def scene(s):
  info=(Q*8)();assert sinfo(s,info);commands=[];owners={}
  for i in range(info[3]):
   m=(Q*16)();o=(Q*5)();identity_fields=(U*5)();assert command_info(s,i,m) and identity(s,i,o,identity_fields)
   owners[m[0]]=tuple(o);commands.append((tuple(m),tuple(o),tuple(identity_fields)))
  return tuple(info),commands,owners
 ai,aa,ao=scene(old);bi,bb,bo=scene(new)
 valid=ai[0]==bi[0] and 0<bi[1]-ai[1]<=8 and ai[2]==bi[2] and ai[7]==bi[7]
 if valid:
  for role in ao:
   x,y=ao[role],bo[role];valid=valid and (x==y or (y[1]>x[1] and 0<y[3]-x[3]<=8))
 pair=pair_prepare(old,new,128*1024)
 if not valid:assert not pair;pair_counts['barrier_rejections']+=1;return
 assert pair;pi=(Q*16)();assert pair_info(pair,pi);pair_counts['accepted_pairs']+=1
 key=lambda c:(c[0][0],c[2]);ac=Counter(map(key,aa));bc=Counter(map(key,bb));oldseen=Counter();newseen=Counter();copied=[]
 for j in range(pi[5]):
  row=(Q*8)();identity_fields=(U*5)();assert pair_row(pair,j,row,identity_fields);status,oi,ni,role,flags,oldorder,neworder,kind=row
  assert oi!=0xffffffff or ni!=0xffffffff
  a=aa[oi] if oi!=0xffffffff else None;b=bb[ni] if ni!=0xffffffff else None;c=a or b;k=key(c)
  assert tuple(identity_fields)==c[2] and role==c[0][0] and kind==c[2][0]
  if a:oldseen[oi]+=1
  if b:newseen[ni]+=1
  if ac[k]>1 or bc[k]>1:assert status==4 and not(a and b)
  elif a and b:assert status==(5 if a[1]==b[1] else 1) and key(a)==key(b)
  elif a:assert status==2 and bc[k]==0
  else:assert status==3 and ac[k]==0
  assert oldorder==(a[0][15] if a else 0xffffffff) and neworder==(b[0][15] if b else 0xffffffff)
  pair_counts['status_'+str(status)]+=1;copied.append((tuple(row),tuple(identity_fields)))
 assert oldseen==Counter({i:1 for i in range(len(aa))}) and newseen==Counter({i:1 for i in range(len(bb))})
 for ep,owners in enumerate([ao,bo]):
  for role,k in owners.items():
   v=(Q*5)();assert pair_owner(pair,role,ep,v) and tuple(v)==k
 sentinel=(Q*8)(*[0xa5a5a5a5]*8);ids=(U*5)(*[0xb6b6b6b6]*5)
 assert not pair_row(pair,pi[5],sentinel,ids) and list(sentinel)==[0xa5a5a5a5]*8 and list(ids)==[0xb6b6b6b6]*5
 assert not pair_row(pair,0,None,ids) and not pair_row(None,0,sentinel,ids)
 if held_pair:pair_free(held_pair)
 held_pair=pair;held_pair_rows=copied
'''
text=text.replace("rom=root.parent/",inject+"\nrom=root.parent/",1)
old='    if held:scene_free(held)';assert text.count(old)==1;text=text.replace(old,'    if held:check_pair(held,scene);scene_free(held)')
marker='assert protected=={str(p):sha(p) for p in [rom,state]}'
addition=r'''
assert held_pair and pair_counts['accepted_pairs']>0 and pair_counts['barrier_rejections']>0
assert pair_counts['accepted_pairs']+pair_counts['barrier_rejections']==scenes-1
# Both scenes, every source frame and core are now destroyed.
for j,e in enumerate(held_pair_rows):
 row=(Q*8)();ids=(U*5)();assert pair_row(held_pair,j,row,ids) and (tuple(row),tuple(ids))==e
pair_free(held_pair)
(out/'real-pair-report.json').write_text(json.dumps(dict(result='PASS_REAL_SCENE_SOURCE_PAIR_TRANSITIONS',counts=dict(pair_counts),scene_source_and_core_destruction_survived=True,all_old_and_new_commands_accounted_once=True,original_frames_and_pcm_exact=True,build_exe_sha256=b['exe_sha256'],core_sha256=b['core_sha256'],dll_sha256=b['identity_dll_sha256'],test_sha256=sha(Path(__file__)),full_scene_60fps=False,motion_enabled=False),indent=2))
print('REAL_SCENE_PAIR_COUNTS',dict(pair_counts),flush=True)
'''
assert text.count(marker)==1;text=text.replace(marker,addition+'\n'+marker)
path=out/('real-scene-pair-'+hashlib.sha256(text.encode('utf-8')).hexdigest()[:12]+'.py')
if path.exists():assert path.read_text(encoding='utf-8')==text
else:path.write_text(text,encoding='utf-8')
r=subprocess.run([os.sys.executable,str(path)],capture_output=True,text=True,timeout=90);(out/'real-pair-verified.log').write_text(r.stdout+r.stderr);print(r.stdout+r.stderr,flush=True);r.check_returncode()
