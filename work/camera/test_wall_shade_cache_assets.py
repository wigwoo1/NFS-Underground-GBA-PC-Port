"""Compare complete captured wall assets across exact-input lookup cache states."""
from pathlib import Path
import ctypes as C,json,runpy,sys,hashlib
p=Path('work/camera');sys.path.insert(0,str(p.resolve()));sys.argv=['oracle','0.5','motion','road-full']
fixture=p/'test_sampled_object_dispatch.py';source=fixture.read_text();marker=' d.nf_draw_palettes_create.argtypes=';assert source.count(marker)==1
# Run fixture setup and original full-asset checks only. Packet assembly is a separate failing gate.
ns={'__name__':'wall_asset_fixture','__file__':str(fixture)};exec(compile(source.split(marker)[0],str(fixture),'exec'),ns);d=ns['d'];P=C.c_void_p;Z=C.c_size_t
crt=C.CDLL('msvcrt');crt._putenv_s.argtypes=[C.c_char_p,C.c_char_p]
f=d.nf_extract_scene_command_full;f.argtypes=[P,ns['Read'],P,P,P,C.POINTER(P),C.POINTER(Z),C.POINTER(P),C.POINTER(Z),P];d.nf_surface_free.argtypes=[P]
checks=[]
for command in ns['commands'][:ns['command_count'].value]:
 if command.kind!=2:continue
 outputs=[]
 for enabled in (False,True,True):
  assert crt._putenv_s(b'NF_TEST_WALL_SHADE_LOOKUP_CACHE',b'1' if enabled else b'')==0
  a=P();az=Z();l=P();lz=Z()
  assert f(C.byref(command),ns['immutable_reader'],None,ns['model_inputs'][48:],ns['model_inputs'][:48],C.byref(a),C.byref(az),C.byref(l),C.byref(lz),None)
  try:outputs.append((C.string_at(a,az.value),C.string_at(l,lz.value) if lz.value else b''))
  finally:d.nf_surface_free(a);d.nf_surface_free(l)
 assert outputs[0]==outputs[1]==outputs[2]
 checks.append(dict(source=command.source,surface_bytes=len(outputs[0][0]),lighting_bytes=len(outputs[0][1]),sha256=hashlib.sha256(b''.join(outputs[0])).hexdigest()))
assert checks and any(c['lighting_bytes']>4 for c in checks)
report=dict(result='PASS_CAPTURED_WALL_CACHE_OUTPUTS',walls=len(checks),checks=checks,scope='Captured midpoint world walls, all output bytes including16lightplanes; broader routes and smooth60fps/physicalXbox not verified')
(p/'wall-shade-cache-assets-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
