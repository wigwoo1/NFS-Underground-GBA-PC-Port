from pathlib import Path
import ctypes as C,struct,json
from scene_batches import batches
root=Path('work/camera');d=C.CDLL(str((root/'visibility-probe-wide.dll').resolve()));Reader=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
d.nf_extract_wall.argtypes=[Reader,C.c_void_p]+[C.c_uint32]*6+[C.POINTER(C.c_void_p),C.POINTER(C.c_size_t)]*2;d.nf_surface_free.argtypes=[C.c_void_p]
d.nf_wall_write_states_owned.argtypes=[Reader,C.c_void_p,C.c_uint32,C.c_uint,C.POINTER(C.c_void_p)]+[C.POINTER(C.c_uint32)]*3

U=C.c_uint32;P=C.c_void_p
class Command(C.Structure):
 _fields_=[('head',U*13),('record',C.c_uint8*16),('state',C.c_uint8*256),('model',C.c_uint8*68),('billboard',U*18),('vertex_count',U),('edge',C.c_uint8*52),('vertices',C.c_int32*(128*6)),('bounds',C.c_uint16*4),('cell_end',U)]
d.nf_extract_scene_command_full.argtypes=[P,Reader,P,P,P,P,P,P,P,P]
d.nf_scene_command_wall_indices_owned.argtypes=[P,Reader,P,C.POINTER(P)]+[C.POINTER(U)]*3

regions=[]
@Reader
def read(context,address,out,size):
 for base,data in regions:
  if base<=address and address+size<=base+len(data):C.memmove(out,data[address-base:address-base+size],size);return 1
 return 0
checked=0;lit_count=0;total=0;state_bytes=0;output_index_bytes=0;output_color_checks=0;palette_geometry_checks=0
for scene in batches(root/'shading.bin'):
 packet=(root/'packet-sequence'/f"scene-{scene['serial']:03}.packet").read_bytes();wo,ws=struct.unpack_from('<2I',packet,48);lo,ls=struct.unpack_from('<2I',packet,72);world=packet[wo:wo+ws];lighting=packet[lo:lo+ls];wp=lp=8
 roads=sum(e['pc']==0x030032f0 for e in scene['events'])
 for _ in range(roads):n,w,h=struct.unpack_from('<3I',world,wp);wp+=12+n*40+w*h*4;assert struct.unpack_from('<I',lighting,lp)[0]==0;lp+=4
 active={}
 for e in scene['events']:
  b=e['blocks']
  if e['pc']==0x03001800:active[b[1][0]]=b
  if e['pc']!=0x03000304:continue
  n,w,h=struct.unpack_from('<3I',world,wp);size=12+n*40+w*h*4;expected=world[wp:wp+size];wp+=size
  lit=struct.unpack_from('<I',lighting,lp)[0];light_size=20+w*h*64 if lit else 4;expected_light=lighting[lp:lp+light_size];lp+=light_size
  parent=active[b[1][0]];regions=[value for value in b.values() if value[1]]+[value for value in parent.values() if value[1]]
  out=C.c_void_p();out_size=C.c_size_t();light=C.c_void_p();light_length=C.c_size_t()
  assert d.nf_extract_wall(read,None,b[1][0],parent[4][0],b[5][0],b[8][0],b[4][0],e['regs'][2],C.byref(out),C.byref(out_size),C.byref(light),C.byref(light_length)),e['id']
  assert C.string_at(out,out_size.value)==expected,('surface',e['id'])
  assert C.string_at(light,light_length.value)==expected_light,('lighting',e['id'])
  # Original event's region descriptor identifies owner directly.
  command=Command();command.head[0]=2;command.head[5]=b[5][0];command.head[6]=e['regs'][2];command.head[9]=b[4][0]
  state_data=b[1][1];material=b[8][1];C.memmove(command.state,state_data,256)
  descriptor_base=struct.unpack_from('<I',state_data,20)[0];region=(parent[4][0]-descriptor_base)//48;assert descriptor_base+region*48==parent[4][0]
  struct.pack_into('<H',command.record,0,region)
  command.head[10]=struct.unpack_from('<I',material,40)[0];command.head[11],command.head[12]=struct.unpack_from('<2H',material,36)
  palette=next(data for base,data in regions if base==0x05000000 and len(data)>=512)[:512]
  owned=P();owned_size=C.c_size_t();owned_light=P();owned_light_size=C.c_size_t();stage=U()
  assert d.nf_extract_scene_command_full(C.byref(command),read,None,palette,None,C.byref(owned),C.byref(owned_size),C.byref(owned_light),C.byref(owned_light_size),C.byref(stage)),(e['id'],stage.value)
  try:
   assert C.string_at(owned,owned_size.value)==expected
   assert C.string_at(owned_light,owned_light_size.value)==expected_light
   # Change every palette color while preserving this actual command/reader.
   # Only expanded RGB may change; vertices/UVs and column lighting parameters
   # must remain exact before an indexed entrant policy can be considered.
   changed_palette=bytes(v^255 for v in palette)
   alternate=P();alternate_size=C.c_size_t();alternate_light=P();alternate_light_size=C.c_size_t()
   assert d.nf_extract_scene_command_full(C.byref(command),read,None,changed_palette,None,C.byref(alternate),C.byref(alternate_size),C.byref(alternate_light),C.byref(alternate_light_size),C.byref(stage))
   try:
    alternate_data=C.string_at(alternate,alternate_size.value);alternate_lighting=C.string_at(alternate_light,alternate_light_size.value)
    assert alternate_size.value==len(expected) and alternate_light_size.value==len(expected_light)
    assert alternate_data[:12+n*40]==expected[:12+n*40],('palette changed geometry/UV',e['id'])
    assert alternate_data[12+n*40+3::4]==expected[12+n*40+3::4],('palette changed alpha',e['id'])
    assert alternate_lighting[:20 if lit else 4]==expected_light[:20 if lit else 4],('palette changed column lighting',e['id'])
    if lit:assert alternate_lighting[23::4]==expected_light[23::4]
    palette_geometry_checks+=1
   finally:d.nf_surface_free(alternate);d.nf_surface_free(alternate_light)
  finally:d.nf_surface_free(owned);d.nf_surface_free(owned_light)
  states=C.c_void_p();sw=C.c_uint32();sh=C.c_uint32();planes=C.c_uint32()
  assert d.nf_wall_write_states_owned(read,None,b[8][0],e['regs'][2],C.byref(states),C.byref(sw),C.byref(sh),C.byref(planes))
  assert (sw.value,sh.value,planes.value)==(w,h,17 if lit else 1)
  # This retained table never maps nonzero input to output index0 (verified
  # separately); alpha therefore independently determines skip/nonzero here.
  base=expected[12+n*40:]
  classified=bytes(2 if a else 0 for a in base[3::4])
  if lit:classified+=bytes(2 if a else 0 for a in expected_light[23::4])
  assert C.string_at(states,len(classified))==classified,('write states',e['id'])
  output_indices=P();iw=U();ih=U();ip=U()
  assert d.nf_scene_command_wall_indices_owned(C.byref(command),read,None,C.byref(output_indices),C.byref(iw),C.byref(ih),C.byref(ip))
  try:
   assert (iw.value,ih.value,ip.value)==(w,h,17 if lit else 1)
   index_data=C.string_at(output_indices,w*h*ip.value)
   texture=next(data for address,data in regions if address<=command.head[10] and command.head[10]+w*h<=address+len(data))
   texture_region=next(address for address,data in regions if address<=command.head[10] and command.head[10]+w*h<=address+len(data))
   source_indices=texture[command.head[10]-texture_region:command.head[10]-texture_region+w*h]
   assert index_data[:w*h]==source_indices
   if lit:
    original_context=C.create_string_buffer(24);original_table=C.create_string_buffer(4096)
    assert read(None,struct.unpack_from('<I',material,8)[0],original_context,24)
    assert read(None,struct.unpack_from('<I',original_context.raw,20)[0],original_table,4096)
    expected_indices=bytes(original_table.raw[index*16+level] if index else 0 for level in range(16) for index in source_indices)
    assert index_data[w*h:]==expected_indices,('original shading table indices',e['id'])
   for plane in range(ip.value):
    plane_rgba=base if plane==0 else expected_light[20+(plane-1)*w*h*4:20+plane*w*h*4]
    for pixel,index in enumerate(index_data[plane*w*h:(plane+1)*w*h]):
     if not source_indices[pixel]:continue # skip has no displayed color
     color=struct.unpack_from('<H',palette,index*2)[0]
     rgb=bytes(((color>>(k*5))&31)*255//31 for k in range(3))
     assert plane_rgba[pixel*4:pixel*4+3]==rgb,('output index color',e['id'],plane,pixel)
     output_color_checks+=1
   output_index_bytes+=len(index_data)
  finally:d.nf_surface_free(output_indices)
  d.nf_surface_free(states);state_bytes+=len(classified)
  d.nf_surface_free(out);d.nf_surface_free(light);checked+=1;lit_count+=bool(lit);total+=size+light_size
bad=P(123);badsize=C.c_size_t(456);badlight=P(789);badlightsize=C.c_size_t(987)
struct.pack_into('<H',command.record,0,65535)
assert not d.nf_extract_scene_command_full(C.byref(command),read,None,palette,None,C.byref(bad),C.byref(badsize),C.byref(badlight),C.byref(badlightsize),C.byref(stage))
assert (bad.value,badsize.value,badlight.value,badlightsize.value)==(123,456,789,987)
struct.pack_into('<H',command.record,0,region);command.head[5]=0
assert not d.nf_extract_scene_command_full(C.byref(command),read,None,palette,None,C.byref(bad),C.byref(badsize),C.byref(badlight),C.byref(badlightsize),C.byref(stage))
assert (bad.value,badsize.value,badlight.value,badlightsize.value)==(123,456,789,987)
assert checked
report={'result':'PASS','wall_records':checked,'shaded_wall_records':lit_count,'palette_geometry_uv_lighting_invariance_checks':palette_geometry_checks,'identical_surface_and_lighting_bytes':total,'exact_write_state_bytes':state_bytes,'output_index_bytes_exact':output_index_bytes,'output_index_color_checks':output_color_checks,'scope':'Explicit command region owner versus728 original-event packet surface/lighting records, exact original source/shading table indices and used RGB; inverted palette preserves geometry/UV/alpha/column lighting. Invalid owner/source atomic rejection. Does not prove actual entering command reader completeness or frontend GPU/timing.'}
(root/'command-wall-region-owner-tests.json').write_text(json.dumps(report,indent=2));print(report)
