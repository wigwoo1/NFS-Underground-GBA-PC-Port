"""Changed/missing consumed asset reads must invalidate the equality shortcut."""
from pathlib import Path
import ctypes as C,json,runpy,sys
p=Path('work/camera');sys.path.insert(0,str(p.resolve()));sys.argv=['oracle','0.5','motion','road-full']
n=runpy.run_path(str(p/'test_sampled_object_dispatch.py'));d=n['d'];P=C.c_void_p;Z=C.c_size_t;Read=n['Read']
match=d.nf_memory_read_matches;match.argtypes=[Read,P,C.c_uint32,P,Z,P,Z]
extract=d.nf_extract_scene_command_full;extract.argtypes=[P,Read,P,P,P,C.POINTER(P),C.POINTER(Z),C.POINTER(P),C.POINTER(Z),P]
records=[]
@Read
def consumed_reader(ctx,address,out,size):
 ok=n['immutable_reader'](ctx,address,out,size)
 if ok:records.append((address,C.string_at(out,size)))
 return ok
cases=[]
for command in n['commands']:
 if command.kind not in (1,2):continue
 a=P();az=Z();l=P();lz=Z();records.clear()
 assert extract(C.byref(command),consumed_reader,None,n['model_inputs'][48:],n['model_inputs'][:48],C.byref(a),C.byref(az),C.byref(l),C.byref(lz),None)
 kind='road' if command.kind==1 else 'lit_wall' if lz.value>4 else 'unlit_wall'
 d.nf_surface_free(a);d.nf_surface_free(l)
 if kind in cases:continue
 cases.append(kind)
 for address,data in list(records):
  if not data:continue
  original=C.create_string_buffer(data,len(data));scratch=C.create_string_buffer(len(data));mode=['equal'];which=[0]
  @Read
  def retained_reader(ctx,addr,out,size):
   assert addr==address and size==len(data)
   if mode[0]=='missing':return 0
   changed=bytearray(data)
   if mode[0]=='changed':changed[which[0]]^=1
   C.memmove(out,bytes(changed),size);return 1
  assert match(retained_reader,None,address,original,len(data),scratch,len(data))
  mode[0]='changed'
  for offset in {0,len(data)-1}:
   which[0]=offset;assert not match(retained_reader,None,address,original,len(data),scratch,len(data));assert original.raw==data
  mode[0]='missing';assert not match(retained_reader,None,address,original,len(data),scratch,len(data))
  assert not match(retained_reader,None,address,original,len(data),scratch,len(data)-1)
  assert not match(retained_reader,None,0xffffffff,original,max(2,len(data)),scratch,len(data))
 assert len(records)>0
 if len(cases)==3:break
assert set(cases)=={'road','unlit_wall','lit_wall'}
report=dict(result='PASS',asset_kinds=cases,scope='Exact consumed-input guard used by live shortcut: captured road/unlit/lit wall reads, first/last byte changes, unavailable reads, insufficient scratch and address overflow all reject. Does not inject mismatch into a running game scene.')
(p/'surface-input-mismatch-tests.json').write_text(json.dumps(report,indent=2));print(report)
