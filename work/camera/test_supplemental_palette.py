import json,struct
from dataclasses import replace
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_closed_supplements import ClosedSupplements
from owned_complete_supplemental_projection import projection_input
from owned_supplemental_rom_geometry import recover_geometry
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();checks=[];negative=0
for f in r['wall_diagnostic_frames']:
 c=ClosedGraph.decode(Path(f['graph']).read_bytes());s=ClosedSupplements.decode(Path(f['supplements']).read_bytes(),c)
 for descriptor in recover_geometry(c,rom):
  raw,sources=projection_input(c,s,rom,descriptor,(1,238,1,158));used=set().union(*(set(w.texture)-{0} for w in sources))
  assert used
  palette=raw[464:976];assert all(palette[i*2:i*2+2]==c.graph.context[384+i*2:386+i*2] for i in used)
  index=min(used);context=bytearray(c.graph.context);context[384+index*2]^=1;bad=replace(c,graph=replace(c.graph,context=bytes(context)))
  try:projection_input(bad,s,rom,descriptor,(1,238,1,158))
  except ValueError:negative+=1
  else:raise AssertionError('Opaque palette mismatch accepted')
 checks.append(dict(refresh=c.refresh,descriptors=16))
out=dict(result='PASS_COMPLETE_SUPPLEMENTAL_OPAQUE_PALETTE',checks=checks,opaque_color_mutations_rejected=negative,scope='All256 complete descriptor/scene palette closures agree for nonzero texels; index0 is discarded by existing wall alpha test. Arbitrary palette changes reject.')
Path('work/camera/supplemental-opaque-palette-tests.json').write_text(json.dumps(out,indent=2));print(out['result'],negative)
