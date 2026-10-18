"""Capture original draw-entry scratch and terminal calls without matching images."""
from pathlib import Path
import ctypes as C,csv,json,struct,hashlib
from scene_batches import records
p=Path('work/camera').resolve();out=p.parents[1]/'outputs/nfsug-native-renderer/camera-research'
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');save=p.parent/'driving.state'
hashes=[hashlib.sha256(x.read_bytes()).hexdigest() for x in (rom,save)]
d=C.CDLL(str(p.parent/'nfsprobe.dll'));d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_world_trace.argtypes=[C.c_char_p]
assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(save).encode(),0)
trace=p/'original-prepared-wall-scene9.bin'
try:
 for row in csv.DictReader((p/'prototype-runs/threaded-923c5fa0b0c14d9292907cbf8e50cc13-input.csv').open()):
  if int(row['before'])==8877:assert d.nf_world_trace(str(trace).encode())
  d.nf_frame(int(row['keys']))
  if int(row['after'])==8882:break
 else:raise AssertionError('Missing interval')
 d.nf_world_trace(None)
finally:d.nf_close()
assert hashes==[hashlib.sha256(x.read_bytes()).hexdigest() for x in (rom,save)]
sources={0x085747fc,0x08574840,0x08574884,0x085748c8,0x0857c6f4};selected=[];active=None
for event in records(trace):
 if event['pc']==0x03000304:
  active=None;blocks=event['blocks'];source=blocks[5][0]
  if source not in sources or event['frame']<=8877:continue
  scratch=blocks[6][1];state=blocks[1][1]
  active=dict(source=hex(source),refresh=event['frame'],arguments=event['regs'][:4],scratch_hex=scratch.hex(),projected_xy_depth=list(struct.unpack_from('<8h',scratch)),flags=struct.unpack_from('<H',scratch,48)[0],bounds=list(struct.unpack_from('<4H',state,226)),terminal_columns=[])
  selected.append(active)
 elif event['pc'] in (0x030053e8,0x03005320) and active is not None:
  active['terminal_columns'].append(dict(pc=hex(event['pc']),destination=hex(event['regs'][1]),starting_v=event['regs'][2],rows=event['regs'][3]))
assert len(selected)==5
recovered=json.loads((out/'native-wall-invocation-audit.json').read_text());comparison=[]
for wall in selected:
 edge=next(e for r in recovered['suspect_regions'] if r['pose']=='older' for e in r['edges'] if e['source']==wall['source'])
 comparison.append(dict(source=wall['source'],actual_edge=wall['projected_xy_depth'],reconstructed_edge=edge['projected_xy_depth'],exact_scratch_match=wall['scratch_hex']==edge['scratch_hex'],actual_columns=len(wall['terminal_columns'])))
report=dict(result='CAPTURED',walls=selected,comparisons=comparison,rom_state_unchanged=True,scope='Actual original prepared wall entry records and terminal column calls. No image-polygon matching; reconstructed retained edges are compared as diagnostic original command data.')
(out/'original-prepared-wall-audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(comparison,indent=2))
