from pathlib import Path
import ctypes as C,struct,json,hashlib,collections
root=Path('work').resolve();d=C.CDLL(str(root/'camera/visibility-probe.dll'));rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');Sink=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint64,C.c_void_p,C.c_size_t)
d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_native_scene_sink.argtypes=[Sink,C.c_void_p]
previous=None;counts=collections.Counter();examples=[];errors=[];duplicates=[];multiplicity=[];texture_updates=[]
order_boundaries=[];boundary_scenes=[]
def reversed_pairs(before,after):
 common=set(before)&set(after);rank={key:i for i,key in enumerate(after)}
 shared=[key for key in before if key in common]
 return [(a,b) for i,a in enumerate(shared) for b in shared[i+1:] if rank[a]>rank[b]]
assert reversed_pairs(['a','b','c'],['c','a','b'])==[('a','c'),('b','c')]
assert reversed_pairs(['a','b'],['a','x','b'])==[]
def texture_delta(before,after):
 assert len(before)==len(after) and len(before)%4==0
 forward={};reverse={};changed=alpha=0;conflicts=False
 for offset in range(0,len(before),4):
  a=before[offset:offset+4];b=after[offset:offset+4]
  changed+=a!=b;alpha+=a[3]!=b[3]
  if a in forward and forward[a]!=b:conflicts=True
  forward[a]=b;reverse.setdefault(b,set()).add(a)
 return dict(pixels=len(before)//4,changed=changed,alpha_changed=alpha,consistent_color_remap=not conflicts,before_colors=len(forward),after_colors=len(reverse))
assert texture_delta(bytes([1,2,3,255])*2,bytes([3,2,1,255])*2)['consistent_color_remap']
assert not texture_delta(bytes([1,2,3,255])*2,bytes([3,2,1,255,4,5,6,255]))['consistent_color_remap']
@Sink
def receive(user,epoch,ptr,size):
 global previous
 try:
  b=C.string_at(ptr,size);h=struct.unpack_from('<8I',b);sections={tag:b[off:off+n] for tag,off,n in [struct.unpack_from('<3I',b,32+i*12) for i in range(5)]};world=sections[2];ids=sections[5];n=struct.unpack_from('<I',world,4)[0];pos=8;current={}
  order=sections[3];commands=struct.unpack_from('<I',order,4)[0]
  positions={}
  for command in range(commands):
   index=struct.unpack_from('<I',order,8+command*4)[0]
   if index!=0xffffffff:
    assert index<n and index not in positions
    positions[index]=command
  assert len(positions)==n
  lighting=sections[4];lp=8;lights=[]
  assert struct.unpack_from('<I',lighting,4)[0]==n
  for i in range(n):
   lit=struct.unpack_from('<I',lighting,lp)[0];assert lit in (0,1)
   length=4 if not lit else 20+struct.unpack_from('<I',lighting,lp+12)[0]*struct.unpack_from('<I',lighting,lp+16)[0]*64
   lights.append(hashlib.sha256(lighting[lp:lp+length]).digest());lp+=length
  assert lp+32768*4==len(lighting)
  for i in range(n):
   count,w,ht=struct.unpack_from('<3I',world,pos);identity=struct.unpack_from('<5I',ids,8+i*20);length=12+count*40+w*ht*4
   geometry=world[pos+12:pos+12+count*24];uv=world[pos+12+count*24:pos+12+count*40];texture=world[pos+12+count*40:pos+length]
   if identity in current:counts['duplicate_ids']+=1
   current.setdefault(identity,[]).append((geometry,uv,hashlib.sha256(texture).digest(),lights[i],world[pos:pos+12],positions[i],texture));pos+=length
  assert pos==len(world)
  ordered=[tuple(struct.unpack_from('<5I',ids,8*1+index*20)) if index!=0xffffffff else ('model',) for index in struct.unpack_from('<'+'I'*commands,order,8)]
  if 51<=h[4]<=55 or 60<=h[4]<=62 or 140<=h[4]<=142:
   boundary_scenes.append(dict(serial=h[4],begin=h[5],end=h[6],order=ordered))
   (root/'camera'/('order-boundary-%d.bin'%h[4])).write_bytes(b)
  for identity,draws in current.items():
   if len(draws)>1:
    differences=[name for j,name in enumerate(['geometry','uv','texture','lighting','dimensions']) if any(a[j]!=draws[0][j] for a in draws[1:])]
    counts['duplicate_different_payloads' if differences else 'duplicate_identical_payloads']+=len(draws)-1
    duplicates.append(dict(serial=h[4],identity=list(identity),commands=[a[5] for a in draws],differences=differences))
  counts['scenes']+=1;counts['world_draws']+=n
  if previous:
   old_serial,old,old_order=previous;counts['boundaries']+=1;counts['entered_ids']+=len(current.keys()-old.keys());counts['exited_ids']+=len(old.keys()-current.keys())
   unique=set(k for k in ordered if ordered.count(k)==1)&set(k for k in old_order if old_order.count(k)==1)
   inversions=reversed_pairs([k for k in old_order if k in unique],[k for k in ordered if k in unique])
   counts['unique_order_inversions']+=len(inversions)
   if inversions:
    counts['order_change_boundaries']+=1
    order_boundaries.append(dict(before=old_serial,after=h[4],inversions=inversions))
   for identity in current.keys()&old.keys():
    counts['shared_ids']+=1
    if len(current[identity])!=len(old[identity]):
     counts['multiplicity_changes']+=1
     multiplicity.append(dict(before=old_serial,after=h[4],identity=list(identity),old_commands=[a[5] for a in old[identity]],new_commands=[a[5] for a in current[identity]]));continue
    for a,z in zip(old[identity],current[identity]):
     counts['shared_draws']+=1
     if a[2]!=z[2] and len(a[6])==len(z[6]):
      texture_updates.append(dict(before=old_serial,after=h[4],identity=list(identity),**texture_delta(a[6],z[6])))
     for j,key in enumerate(['geometry_changes','uv_changes','texture_changes','lighting_changes','dimension_changes']):
      if a[j]!=z[j]:
       counts[key]+=1
       if len(examples)<20:examples.append(dict(before=old_serial,after=h[4],identity=list(identity),change=key))
  previous=(h[4],current,ordered);return 1
 except Exception as e:errors.append(repr(e));return 0
assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(root/'driving.state').encode(),0)
try:
 assert d.nf_native_scene_sink(receive,None)
 for frame in range(850):d.nf_frame(1|(32 if 180<=frame<500 else 16 if 500<=frame<720 else 0))
 assert not errors,errors
finally:d.nf_close()
report=dict(result='PASS',counts=dict(counts),examples=examples,duplicates=duplicates,multiplicity=multiplicity,texture_updates=texture_updates,order_boundaries=order_boundaries,boundary_scenes=boundary_scenes,scope='Identity-based source world record continuity. Order inversion audit excludes identities duplicated at either endpoint; includes model marker. Changed order is diagnostic, not a rendering defect assertion. Color remaps do not prove palette-only updates. Visibility changes remain unverified.')
(root/'camera/world-continuity-tests.json').write_text(json.dumps(report,indent=2));print(report)

