from pathlib import Path
import ctypes as C,struct,json,random
class Section(C.Structure):_fields_=[('data',C.c_void_p),('size',C.c_size_t)]
class View(C.Structure):_fields_=[('serial',C.c_uint32),('begin',C.c_uint32),('end',C.c_uint32),('page',C.c_uint32),('sections',Section*5)]
class Time(C.Structure):_fields_=[('epoch',C.c_uint64),('older',C.c_uint64),('newer',C.c_uint64),('alpha',C.c_double),('target',C.c_double)]
class Pair(C.Structure):_fields_=[('time',Time),('older',C.c_void_p),('older_size',C.c_size_t),('newer',C.c_void_p),('newer_size',C.c_size_t)]
root=Path('work/camera');data=(root/'scene-packet.bin').read_bytes();d=C.CDLL(str((root/'scene_packet.dll').resolve()))
d.nf_scene_packet_view.argtypes=[C.c_void_p,C.c_size_t,C.POINTER(View)]
def accepted(payload):
 view=View();C.memset(C.byref(view),0xad,C.sizeof(view));before=bytes(view)
 ok=d.nf_scene_packet_view(C.create_string_buffer(bytes(payload)),len(payload),C.byref(view))
 if not ok:assert bytes(view)==before,'Failed parse modified output'
 return ok
assert accepted(data)
rejected=0
for length in [0,31,95,len(data)-1,len(data)//2]:assert not accepted(data[:length]);rejected+=1
model=struct.unpack_from('<I',data,36)[0];world=struct.unpack_from('<I',data,48)[0];order=struct.unpack_from('<I',data,60)[0];lighting=struct.unpack_from('<I',data,72)[0]
for offset,value in [(0,0),(4,2),(8,1),(12,6),(28,2),(36,0),(40,0xffffffff),(44,1),(48,96),(model+4,0xffffffff),(model+8,0),(world+4,129),(world+8,33),(order+8,0xfffffffe),(lighting+4,0)]:
 bad=bytearray(data);struct.pack_into('<I',bad,offset,value);assert not accepted(bad),(offset,value);rejected+=1
bad=bytearray(data);struct.pack_into('<d',bad,model+24,float('nan'));assert not accepted(bad);rejected+=1
d.nf_snapshot_create.argtypes=[C.c_size_t];d.nf_snapshot_create.restype=C.c_void_p
d.nf_snapshot_push.argtypes=[C.c_void_p,C.c_uint64,C.c_uint64,C.c_double,C.c_void_p,C.c_size_t]
d.nf_snapshot_acquire.argtypes=[C.c_void_p,C.c_double,C.c_double,C.POINTER(Pair)]
d.nf_snapshot_release.argtypes=[C.c_void_p];d.nf_snapshot_destroy.argtypes=[C.c_void_p]
d.nf_scene_packet_push.argtypes=[C.c_void_p,C.c_uint64,C.c_void_p,C.c_size_t]
store=d.nf_snapshot_create(len(data)*2);buffer=C.create_string_buffer(data)
assert d.nf_scene_packet_push(store,1,buffer,len(data))
assert not d.nf_scene_packet_push(store,1,buffer,len(data)-1)
C.memset(buffer,0,len(data))
pair=Pair();assert d.nf_snapshot_acquire(store,struct.unpack_from('<I',data,24)[0],0,C.byref(pair))==2
view=View();assert d.nf_scene_packet_view(pair.older,pair.older_size,C.byref(view)) and view.serial==10
assert C.string_at(pair.older,pair.older_size)==data
d.nf_snapshot_release(store);assert d.nf_snapshot_destroy(store)
report={'result':'PASS','packet_bytes':len(data),'malformed_packets_rejected':rejected,'owned_packet_roundtrip':True,'scope':'Supported single-model packet structure and ownership. GPU consumption is tested separately; live extraction remains unfinished.'}
(root/'scene-packet-tests.json').write_text(json.dumps(report,indent=2));print(report)

# Synthetic NSP2 model-count coverage. Reuse the saved valid NFM2 and exercise
# the parser's public ordered model accessors at both supported limits.
sections={}
for i in range(5):
 tag,off,length=struct.unpack_from('<3I',data,32+i*12);sections[tag]=data[off:off+length]
base_model=sections[1];world_count=struct.unpack_from('<I',sections[2],4)[0]
old_order_count=struct.unpack_from('<I',sections[3],4)[0]
old_order=list(struct.unpack_from('<'+'I'*old_order_count,sections[3],8))
assert old_order.count(0xffffffff)==1
ids=sections[5];old_ids_count=struct.unpack_from('<I',ids,4)[0]
assert old_ids_count==world_count+1 and len(ids)==8+old_ids_count*20
model_identity=ids[8+world_count*20:8+(world_count+1)*20]
def _nsp2_packet(n,model_keys=None,include_world=True):
 if model_keys is None:model_keys=list(range(n))
 assert len(model_keys)==n and all(0<=key<n for key in model_keys)
 models=bytearray(8+n*8);struct.pack_into('<II',models,0,0x314c4d4e,n)
 for j in range(n):
  off=(len(models)+7)&~7;models.extend(bytes(off-len(models)));models.extend(base_model)
  struct.pack_into('<II',models,8+j*8,off,len(base_model))
 world_commands=[v for v in old_order if v<0xfffffff0] if include_world else []
 packet_world_count=world_count if include_world else 0
 world_section=sections[2] if include_world else struct.pack('<II',0x31444652,0)
 lighting_section=sections[4] if include_world else struct.pack('<II',0x314c464e,0)+bytes(32768*4)
 assert len(world_commands)==packet_world_count
 model_commands=[0xffffffff-j for j in reversed(range(n))]
 order_values=model_commands+world_commands
 model_draw_order=[0xffffffff-v for v in order_values if v>=0xfffffff0]
 if n<=16: assert model_draw_order==list(reversed(range(n)))
 order=struct.pack('<II',0x314f464e,len(order_values))+struct.pack('<'+'I'*len(order_values),*order_values)
 identities=bytearray(ids[:8+packet_world_count*20]);struct.pack_into('<I',identities,4,packet_world_count+n)
 for key in model_keys:
  row=bytearray(model_identity);struct.pack_into('<I',row,8,0x10000+key);identities.extend(row)
 payload=bytearray(96);serial,begin,end,page=struct.unpack_from('<4I',data,16)
 struct.pack_into('<8I',payload,0,0x3150534e,2,0,5,serial,begin,end,page)
 for i,(tag,blob) in enumerate(((1,bytes(models)),(2,world_section),(3,order),(4,lighting_section),(5,bytes(identities)))):
  off=(len(payload)+7)&~7;payload.extend(bytes(off-len(payload)));struct.pack_into('<3I',payload,32+i*12,tag,off,len(blob));payload.extend(blob)
 struct.pack_into('<I',payload,8,len(payload));return bytes(payload)
d.nf_scene_packet_model_count.argtypes=[C.POINTER(View)];d.nf_scene_packet_model_count.restype=C.c_uint
d.nf_scene_packet_model.argtypes=[C.POINTER(View),C.c_uint,C.POINTER(Section)];d.nf_scene_packet_model.restype=C.c_int
multi_results={}
for n in (2,16):
 payload=_nsp2_packet(n);assert accepted(payload)
 owner=C.create_string_buffer(payload);view=View();assert d.nf_scene_packet_view(owner,len(payload),C.byref(view))
 assert d.nf_scene_packet_model_count(C.byref(view))==n
 for j in range(n):
  item=Section();assert d.nf_scene_packet_model(C.byref(view),j,C.byref(item))
  assert C.string_at(item.data,item.size)==base_model
 sentinel=Section(C.c_void_p(0x12345678),999);before=bytes(sentinel)
 assert not d.nf_scene_packet_model(C.byref(view),n,C.byref(sentinel)) and bytes(sentinel)==before
 multi_results[str(n)]={'packet_bytes':len(payload),'models_read':n,'sections_equal_fixture':True,'draw_order_model_indices':list(reversed(range(n)))}
assert not accepted(_nsp2_packet(17))
d.nf_scene_packet_pair_model_indices.argtypes=[C.POINTER(View),C.POINTER(View),C.POINTER(C.c_uint),C.c_size_t]
d.nf_scene_packet_pair_model_indices.restype=C.c_int
old_payload=_nsp2_packet(4);new_payload=_nsp2_packet(4,list(reversed(range(4))))
old_owner=C.create_string_buffer(old_payload);new_owner=C.create_string_buffer(new_payload)
old_view=View();new_view=View()
assert d.nf_scene_packet_view(old_owner,len(old_payload),C.byref(old_view))
assert d.nf_scene_packet_view(new_owner,len(new_payload),C.byref(new_view))
pair_map=(C.c_uint*16)(*([0x55555555]*16))
assert d.nf_scene_packet_pair_model_indices(C.byref(old_view),C.byref(new_view),pair_map,16)
assert list(pair_map)[:4]==[3,2,1,0]
duplicate_payload=_nsp2_packet(4,[0,0,2,3]);duplicate_owner=C.create_string_buffer(duplicate_payload);duplicate_view=View()
assert d.nf_scene_packet_view(duplicate_owner,len(duplicate_payload),C.byref(duplicate_view))
sentinel=(C.c_uint*16)(*([0x55555555]*16));sentinel_before=bytes(sentinel)
assert not d.nf_scene_packet_pair_model_indices(C.byref(old_view),C.byref(duplicate_view),sentinel,16)
assert bytes(sentinel)==sentinel_before
small_payload=_nsp2_packet(2);small_owner=C.create_string_buffer(small_payload);small_view=View()
assert d.nf_scene_packet_view(small_owner,len(small_payload),C.byref(small_view))
assert not d.nf_scene_packet_pair_model_indices(C.byref(old_view),C.byref(small_view),sentinel,16)
assert bytes(sentinel)==sentinel_before
assert not d.nf_scene_packet_pair_model_indices(C.byref(old_view),C.byref(new_view),sentinel,3)
assert bytes(sentinel)==sentinel_before
empty_world_payload=_nsp2_packet(4,list(reversed(range(4))),include_world=False);empty_world_owner=C.create_string_buffer(empty_world_payload);empty_world_view=View()
assert d.nf_scene_packet_view(empty_world_owner,len(empty_world_payload),C.byref(empty_world_view))
world_change_map=(C.c_uint*16)(*([0x55555555]*16))
assert d.nf_scene_packet_pair_model_indices(C.byref(old_view),C.byref(empty_world_view),world_change_map,16)
assert list(world_change_map)[:4]==[3,2,1,0]
# World-surface identity correspondence, including topology changes.
d.nf_scene_packet_pair_world_indices.argtypes=[C.POINTER(View),C.POINTER(View),C.POINTER(C.c_uint),C.c_size_t,C.POINTER(C.c_uint)]
d.nf_scene_packet_pair_world_indices.restype=C.c_int
def _world_identity_offset(payload):
 for i in range(5):
  tag,off,length=struct.unpack_from('<3I',payload,32+i*12)
  if tag==5:return off
 raise AssertionError('identity section missing')
world_n=world_count
world_old=_nsp2_packet(4); world_new=bytearray(world_old); world_idoff=_world_identity_offset(world_new)
for i in range(world_n//2):
 a=world_idoff+8+i*20; b=world_idoff+8+(world_n-1-i)*20
 ra=bytes(world_new[a:a+20]); rb=bytes(world_new[b:b+20]); world_new[a:a+20]=rb; world_new[b:b+20]=ra
world_old_owner=C.create_string_buffer(world_old); world_new_owner=C.create_string_buffer(bytes(world_new)); world_old_view=View(); world_new_view=View()
assert d.nf_scene_packet_view(world_old_owner,len(world_old),C.byref(world_old_view)) and d.nf_scene_packet_view(world_new_owner,len(world_new),C.byref(world_new_view))
world_map=(C.c_uint*max(world_n,1))(); world_matches=C.c_uint(999)
assert d.nf_scene_packet_pair_world_indices(C.byref(world_old_view),C.byref(world_new_view),world_map,world_n,C.byref(world_matches))
assert list(world_map)[:world_n]==list(reversed(range(world_n))) and world_matches.value==world_n
missing_world=bytearray(world_old); missing_off=_world_identity_offset(missing_world); missing_world[missing_off+8+8:missing_off+8+12]=struct.pack('<I',0xdeadbeef)
missing_owner=C.create_string_buffer(bytes(missing_world)); missing_view=View(); assert d.nf_scene_packet_view(missing_owner,len(missing_world),C.byref(missing_view))
assert d.nf_scene_packet_pair_world_indices(C.byref(world_old_view),C.byref(missing_view),world_map,world_n,C.byref(world_matches))
assert world_map[0]==0xffffffff and world_matches.value==world_n-1
ambiguous_world=bytearray(world_old); amb_off=_world_identity_offset(ambiguous_world); ambiguous_world[amb_off+8+20:amb_off+8+40]=ambiguous_world[amb_off+8:amb_off+28]
amb_owner=C.create_string_buffer(bytes(ambiguous_world));amb_view=View();assert d.nf_scene_packet_view(amb_owner,len(ambiguous_world),C.byref(amb_view))
assert d.nf_scene_packet_pair_world_indices(C.byref(world_old_view),C.byref(amb_view),world_map,world_n,C.byref(world_matches))
assert world_map[0]==0xffffffff and world_map[1]==0xffffffff and world_matches.value==world_n-2
empty_world_payload=_nsp2_packet(4,include_world=False);empty_world_owner=C.create_string_buffer(empty_world_payload);empty_world_view=View()
assert d.nf_scene_packet_view(empty_world_owner,len(empty_world_payload),C.byref(empty_world_view))
assert d.nf_scene_packet_pair_world_indices(C.byref(world_old_view),C.byref(empty_world_view),world_map,world_n,C.byref(world_matches))
assert world_matches.value==0 and all(world_map[i]==0xffffffff for i in range(world_n))
short_world=(C.c_uint*max(world_n-1,1))(*([0x55555555]*max(world_n-1,1)));short_before=bytes(short_world);count_sentinel=C.c_uint(77)
assert not d.nf_scene_packet_pair_world_indices(C.byref(world_old_view),C.byref(world_new_view),short_world,world_n-1,C.byref(count_sentinel))
assert bytes(short_world)==short_before and count_sentinel.value==77
world_pairing={'surfaces':world_n,'reversed_identity_mapping':True,'missing_and_duplicate_ids_marked_unmatched':True,'different_world_count_supported':True,'short_capacity_failure_atomic':True}
pairing={'older_to_reordered_newer':[3,2,1,0],'different_world_count_supported':True,'duplicate_identity_rejected':True,'changed_model_count_rejected':True,'short_output_rejected_atomically':True}
report=json.loads((root/'scene-packet-tests.json').read_text())
report.update(nsp2_model_counts_tested=[2,16],nsp2_unsupported_17_rejected=True,nsp2_results=multi_results,nsp2_identity_pairing=pairing,nsp2_world_identity_pairing=world_pairing)
(root/'scene-packet-tests.json').write_text(json.dumps(report,indent=2));print({'nsp2':'PASS','counts':[2,16],'rejected':17,'world_identity':world_pairing})

# Partial correspondence preserves the full older membership while matching only
# unambiguous source identities, including the disappearance of model slot zero.
d.nf_scene_packet_pair_model_subset.argtypes=[C.POINTER(View),C.POINTER(View),C.POINTER(C.c_uint),C.c_size_t,C.POINTER(C.c_uint)]
def subset_owner(keys,include_world=True):
 payload=bytearray(data if len(keys)==1 else _nsp2_packet(len(keys),include_world=include_world))
 identity_off=_world_identity_offset(payload)
 world_off=struct.unpack_from('<I',payload,48)[0]
 nworld=struct.unpack_from('<I',payload,world_off+4)[0]
 for i,key in enumerate(keys):struct.pack_into('<I',payload,identity_off+8+(nworld+i)*20+8,0x10000+key)
 owner=C.create_string_buffer(bytes(payload));view=View()
 assert d.nf_scene_packet_view(owner,len(payload),C.byref(view))
 return owner,view
subset_cases=[
 ([0,1,2,3],[1,3]),([0,1],[2,0,1]),([0],[1,0]),([0,1],[9]),
 ([0,1,2,3],[3,2,1,0]),([0,0,2,3],[0,2,3]),([0,1,2,3],[0,0,2]),
 (list(range(16)),list(reversed(range(16))))
]
rng=random.Random(1541)
for _ in range(80):
 subset_cases.append((rng.sample(range(24),rng.randrange(1,17)),rng.sample(range(24),rng.randrange(1,17))))
for old_keys,new_keys in subset_cases:
 ao,av=subset_owner(old_keys);bo,bv=subset_owner(new_keys)
 actual=(C.c_uint*16)(*([0x55555555]*16));matched=C.c_uint(99)
 assert d.nf_scene_packet_pair_model_subset(C.byref(av),C.byref(bv),actual,16,C.byref(matched))
 expected=[new_keys.index(key) if old_keys.count(key)==new_keys.count(key)==1 else 0xffffffff for key in old_keys]
 assert list(actual)[:len(old_keys)]==expected,(old_keys,new_keys,list(actual),expected)
 assert matched.value==sum(value!=0xffffffff for value in expected)
ao,av=subset_owner([0,1,2,3]);bo,bv=subset_owner([3,1],include_world=False)
actual=(C.c_uint*16)(*([0x55555555]*16));matched=C.c_uint(99)
assert d.nf_scene_packet_pair_model_subset(C.byref(av),C.byref(bv),actual,16,C.byref(matched))
assert list(actual)[:4]==[0xffffffff,1,0xffffffff,0] and matched.value==2
# Invalid input must preserve both outputs.
sentinel=(C.c_uint*16)(*([0x55555555]*16));before=bytes(sentinel)
for invalid in ('short-capacity','short-identity','wrong-model-kind','missing-count-output'):
 bad=View.from_buffer_copy(bytes(bv));count=C.c_uint(77);cap=16;out_count=C.byref(count)
 if invalid=='short-capacity':cap=3
 elif invalid=='short-identity':bad.sections[4].size=8
 elif invalid=='wrong-model-kind':
  owned=C.create_string_buffer(C.string_at(bv.sections[4].data,bv.sections[4].size))
  world_off=struct.unpack('<I',C.string_at(bv.sections[1].data+4,4))[0]
  C.memmove(C.addressof(owned)+8+world_off*20,struct.pack('<I',2),4);bad.sections[4].data=C.addressof(owned)
 else:out_count=None
 assert not d.nf_scene_packet_pair_model_subset(C.byref(av),C.byref(bad),sentinel,cap,out_count)
 assert bytes(sentinel)==before and count.value==77,invalid
report=json.loads((root/'scene-packet-tests.json').read_text())
report['nsp2_model_subset_pairing']=dict(result='PASS',membership_cases=len(subset_cases)+1,invalid_atomic_cases=4,duplicate_ids_never_blended=True,primary_disappearance_supported=True,strict_pairing_behavior_unchanged=True)
(root/'scene-packet-tests.json').write_text(json.dumps(report,indent=2));print(report['nsp2_model_subset_pairing'])
