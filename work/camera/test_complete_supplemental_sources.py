import json
from pathlib import Path
from types import SimpleNamespace
from dataclasses import replace
from owned_closed_graph import ClosedGraph
from owned_closed_supplements import ClosedSupplements
from owned_graph_wall_sources import supplemental_wall_sources
from owned_complete_supplemental_sources import complete_wall_sources
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());checks=[];matched=0
for f in r['wall_diagnostic_frames']:
 c=ClosedGraph.decode(Path(f['graph']).read_bytes());s=ClosedSupplements.decode(Path(f['supplements']).read_bytes(),c)
 sources=complete_wall_sources(c,s,rom);lookup={(w.descriptor,w.edge):w for w in sources}
 proxy=SimpleNamespace(supplements=s.geometry,textures=s.textures,validate=lambda:None)
 for w in supplemental_wall_sources(proxy):assert lookup[w.descriptor,w.edge]==w;matched+=1
 assert len({w.descriptor for w in sources})==16
 for bad in (replace(s,epoch=s.epoch+1),replace(s,textures=b'')):
  try:complete_wall_sources(c,bad,rom)
  except ValueError:pass
  else:raise AssertionError('Incomplete closure accepted')
 checks.append(dict(refresh=c.refresh,descriptors=len({w.descriptor for w in sources}),wall_edges=len(sources)))
out=dict(result='PASS_COMPLETE_SUPPLEMENTAL_WALL_SOURCE_CLOSURE',captured_edges_exact=matched,checks=checks,scope='Complete raw supplemental wall assets for retained scenes; callback eligibility, sampled surface visibility and live GPU integration remain unverified.')
Path('work/camera/complete-supplemental-source-tests.json').write_text(json.dumps(out,indent=2));print(out['result'],matched,checks[0])
