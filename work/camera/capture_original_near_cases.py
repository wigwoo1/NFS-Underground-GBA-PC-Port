"""Capture original prepared draw data for source-defined near-plane cases."""
from pathlib import Path
import ctypes as C,json,struct,hashlib
from scene_batches import batches
p=Path('work/camera').resolve();o=p.parents[1]/'outputs/nfsug-native-renderer/camera-research';cases=json.loads((o/'multimodel-near-plane-cases.json').read_text())['scenes'];first=min(r['identity'][2] for r in cases);last=max(r['identity'][3] for r in cases)
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');save=p.parent/'driving.state';hashes=[hashlib.sha256(f.read_bytes()).hexdigest() for f in (rom,save)]
d=C.CDLL(str(p/'visibility-probe-wide.dll'));d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_native_scene_refresh.restype=C.c_uint;d.nf_world_trace.argtypes=[C.c_char_p];trace=p/'original-multimodel-near-cases.bin';started=False
assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(save).encode(),0)
try:
 for i in range(3583):
  before=d.nf_native_scene_refresh()
  if before>=first-1 and not started:assert d.nf_world_trace(str(trace).encode());started=True
  d.nf_frame(1|(32 if 180<=i<500 else 16 if 500<=i<720 else 0))
  if d.nf_native_scene_refresh()>last:break
 d.nf_world_trace(None)
finally:d.nf_close()
assert hashes==[hashlib.sha256(f.read_bytes()).hexdigest() for f in (rom,save)]
by_interval={(b['begin_refresh'],b['end_refresh']):b for b in batches(trace)};rows=[]
for scene in cases:
 identity=scene['identity'];batch=by_interval[(identity[2],identity[3])]
 for case in scene['crossing_surfaces']:
  source=int(case['source'],16);matches=[]
  for e in batch['events']:
   if case['kind']==1 and e['pc']==0x030032f0 and e['blocks'][4][0]==source:
    b=e['blocks'];matches.append(dict(refresh=e['frame'],pc=hex(e['pc']),descriptor_hex=b[4][1].hex(),prepared_start_count=list(struct.unpack_from('<2H',b[1][1],242)),state_bounds=list(struct.unpack_from('<4H',b[1][1],226)),source_hex=b[5][1].hex(),scratch_hex=b[6][1].hex(),prepared_hex=b[7][1].hex(),material_hex=b[8][1].hex(),animation_hex=b[9][1].hex(),projection_hex=b[3][1].hex()))
   elif case['kind']==2 and e['pc']==0x03000304 and e['blocks'][5][0]==source:
    b=e['blocks'];matches.append(dict(refresh=e['frame'],pc=hex(e['pc']),source_hex=b[5][1].hex(),scratch_hex=b[6][1].hex(),state_bounds=list(struct.unpack_from('<4H',b[1][1],226))))
  assert len(matches)==1,(identity,case,len(matches));rows.append(dict(identity=identity,case=case,original=matches[0]))
assert len(rows)==38
(o/'original-multimodel-near-case-capture.json').write_text(json.dumps(dict(result='CAPTURED',cases=rows,rom_state_unchanged=True,scope='Exact completed scene boundary and source identity joins to actual original prepared draws; projection/UV numeric verification pending'),indent=2));print('captured',len(rows))
