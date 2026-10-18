import json,hashlib
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_closed_supplements import ClosedSupplements
from owned_scene_bundle import chunks
from owned_supplemental_rom_geometry import recover_geometry
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
assert hashlib.sha256(rom).hexdigest().upper()=='53817AEC76A623DC2C7782DDF841F89F369AEBE5A92A28C9AFC69FEAF914A593'
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());checks=[];matched=0
for frame in r['wall_diagnostic_frames']:
 closed=ClosedGraph.decode(Path(frame['graph']).read_bytes());assets=recover_geometry(closed,rom)
 supplements=ClosedSupplements.decode(Path(frame['supplements']).read_bytes(),closed)
 for h,raw in chunks(supplements.geometry,'supplements'):
  asset=assets[h[3]]
  assert asset.raw_descriptor==raw[32:80]
  assert asset.ring==b''.join(raw[976+i*140:1044+i*140] for i in range(h[4]))
  matched+=1
 checks.append(dict(refresh=closed.refresh,assets=[dict(descriptor=a.descriptor,vertices=len(a.ring)//68,offsets=a.offset_indices,materials=a.material_indices) for a in assets.values()]))
assert matched==18
try:recover_geometry(closed,b'')
except ValueError:pass
else:raise AssertionError('Truncated ROM accepted')
out=dict(result='PASS_SUPPLEMENTAL_ROM_GEOMETRY',scenes=len(checks),captured_invocations_exact=matched,checks=checks,scope='Immutable descriptor/ring closure only; RAM offsets, animation/material resolution, textures and sampled dispatch remain dependencies.')
Path('work/camera/supplemental-rom-geometry-tests.json').write_text(json.dumps(out,indent=2));print(out['result'],matched)

