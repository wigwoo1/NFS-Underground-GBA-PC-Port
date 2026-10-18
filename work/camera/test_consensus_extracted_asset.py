"""Consensus validation transfers the exact owned surface and lighting."""
from pathlib import Path
import ctypes as C,json,runpy,sys
p=Path('work/camera');sys.path.insert(0,str(p.resolve()));sys.argv=['oracle','0.5','motion','road-full']
ns=runpy.run_path(str(p/'test_sampled_object_dispatch.py'));d=ns['d'];P=C.c_void_p;Z=C.c_size_t;U=C.c_uint;Read=ns['Read']
d.nf_draw_palettes_create.argtypes=[C.c_uint64,U];d.nf_draw_palettes_create.restype=P
d.nf_draw_palettes_append.argtypes=[P,U,U,U,P,Z];d.nf_draw_palettes_seal.argtypes=[P];d.nf_draw_palettes_destroy.argtypes=[P]
combined=d.nf_scene_command_palette_consensus_extract;combined.argtypes=[P,U,P,U,C.c_uint64,P,Read,P,P,P,C.POINTER(P),C.POINTER(Z),C.POINTER(P),C.POINTER(Z)]
direct=d.nf_extract_scene_command_full;direct.argtypes=[P,Read,P,P,P,C.POINTER(P),C.POINTER(Z),C.POINTER(P),C.POINTER(Z),P]
palette=ns['model_inputs'][48:];rotation=ns['model_inputs'][:48];total=lighting=0
cases=[next(c for c in ns['commands'] if c.kind==kind) for kind in (1,2)]
for candidate in ns['commands']:
 if candidate.kind!=2:continue
 a=P();az=Z();l=P();lz=Z()
 assert direct(C.byref(candidate),ns['immutable_reader'],None,palette,rotation,C.byref(a),C.byref(az),C.byref(l),C.byref(lz),None)
 lit=lz.value>4;d.nf_surface_free(a);d.nf_surface_free(l)
 if lit:cases.append(candidate);break
assert len(cases)==3
for command in cases:
 kind=command.kind
 bank=d.nf_draw_palettes_create(43,17);assert bank
 for _ in range(2):assert d.nf_draw_palettes_append(bank,kind,command.source,command.material[1 if kind==1 else 0],palette,512)
 assert d.nf_draw_palettes_seal(bank)
 a=P();az=Z();l=P();lz=Z();colors=C.create_string_buffer(512)
 assert combined(bank,17,bank,17,43,C.byref(command),ns['immutable_reader'],None,rotation,colors,C.byref(a),C.byref(az),C.byref(l),C.byref(lz)) and colors.raw==palette
 # Wrong epoch must not publish any of the five outputs.
 bad_colors=C.create_string_buffer(b'X'*512,512);ba=P(123);bz=Z(456);bl=P(789);blz=Z(1011)
 assert not combined(bank,17,bank,17,44,C.byref(command),ns['immutable_reader'],None,rotation,bad_colors,C.byref(ba),C.byref(bz),C.byref(bl),C.byref(blz))
 assert bad_colors.raw==b'X'*512 and (ba.value,bz.value,bl.value,blz.value)==(123,456,789,1011)
 d.nf_draw_palettes_destroy(bank)
 expected=P();ez=Z();light=P();sz=Z()
 try:
  assert direct(C.byref(command),ns['immutable_reader'],None,palette,rotation,C.byref(expected),C.byref(ez),C.byref(light),C.byref(sz),None)
  assert az.value==ez.value and C.string_at(a,az.value)==C.string_at(expected,ez.value)
  assert lz.value==sz.value and (not lz.value or C.string_at(l,lz.value)==C.string_at(light,sz.value))
  total+=az.value;lighting+=lz.value
 finally:
  for allocation in (a,l,expected,light):d.nf_surface_free(allocation)
 # Missing identity bank must preserve palette and all four asset outputs.
 bank=d.nf_draw_palettes_create(43,17);assert d.nf_draw_palettes_seal(bank)
 colors.raw=b'X'*512;a=P(123);az=Z(456);l=P(789);lz=Z(1011)
 try:
  assert not combined(bank,17,bank,17,43,C.byref(command),ns['immutable_reader'],None,rotation,colors,C.byref(a),C.byref(az),C.byref(l),C.byref(lz))
  assert colors.raw==b'X'*512 and (a.value,az.value,l.value,lz.value)==(123,456,789,1011)
 finally:d.nf_draw_palettes_destroy(bank)
report=dict(result='PASS',road_unlit_wall_lit_wall_assets=3,exact_surface_bytes=total,exact_lighting_bytes=lighting,ownership_survives_bank_destroy=True,atomic_empty_bank_rejections=3,atomic_epoch_rejections=3,scope='Consensus ownership and atomic failure contract, including all16 lighting variants; does not establish full-scene motion or scanout.')
(p/'consensus-extracted-asset-tests.json').write_text(json.dumps(report,indent=2));print(report)
