from pathlib import Path
import ctypes as C,struct,json
p=Path('work/camera');f=p/'overflow-scene-171';d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()))
d.nf_assembly_create.restype=C.c_void_p
for name in ('nf_assembly_reset','nf_assembly_destroy'):getattr(d,name).argtypes=[C.c_void_p]
d.nf_assembly_surface.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t];d.nf_assembly_bounds.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_void_p]
d.nf_assembly_model.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_size_t];d.nf_assembly_finish.argtypes=[C.c_void_p]+[C.c_uint32]*4+[C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p]
for a in ('0.25','0.5','0.75'):assert (f/f'assembly-owned-{a}.bin').read_bytes()==(f/f'owned-bounds-{a}.bin').read_bytes()
raw=(f/'old.bin').read_bytes();sections={t:raw[o:o+n] for t,o,n in (struct.unpack_from('<3I',raw,32+i*12) for i in range(5))};model=sections[1];table=sections[4][-131072:]
surface=struct.pack('<3I15d4B',3,1,1,*([0.]*15),255,255,255,255);identity=struct.pack('<5I',1,1,1,8,0);bounds=struct.pack('<4H',0,240,0,160);owner=d.nf_assembly_create()
try:
 for mode in ('missing','duplicate','alpha','invalid','index'):
  d.nf_assembly_reset(owner)
  for i in range(2):assert d.nf_assembly_surface(owner,identity,surface,len(surface),struct.pack('<I',0),4)
  assert d.nf_assembly_model(owner,struct.pack('<5I',3,1,1,8,0),model,len(model))
  assert d.nf_assembly_bounds(owner,0,.5,bounds)
  if mode=='duplicate':assert not d.nf_assembly_bounds(owner,0,.5,bounds)
  if mode=='alpha':assert not d.nf_assembly_bounds(owner,1,.25,bounds)
  if mode=='invalid':assert not d.nf_assembly_bounds(owner,1,.5,struct.pack('<4H',0,240,0,161))
  if mode=='index':assert not d.nf_assembly_bounds(owner,2,.5,bounds)
  out=C.c_void_p(123);size=C.c_size_t(456)
  assert not d.nf_assembly_finish(owner,1,1,2,0,table,len(table),C.byref(out),C.byref(size)) and out.value==123 and size.value==456
finally:d.nf_assembly_destroy(owner)
report=dict(result='PASS',assembled_packets_exact=3,partial_or_poisoned_scene_rejections=5,scope='Native assembly publishes identical owned bounds packets; partial/inconsistent bounds cannot publish. Offline source eligibility retained.')
(p/'assembly-bounds-tests.json').write_text(json.dumps(report,indent=2));print(report)
