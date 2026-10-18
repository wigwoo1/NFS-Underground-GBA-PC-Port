import json,struct,gc,weakref,os
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_endpoint_road_planner import EndpointRoadPlanner
from owned_endpoint_road_selection import endpoint_road_span_candidates
assert os.environ.get('NF_NATIVE_ROAD_READER')!='1'
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text())
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);h=EndpointRoadPlanner(rom,table)
class Proxy:
 def __init__(self,m,fail=False):self.memory=m;self.fail=fail
 def read(self,*args):
  if self.fail:raise ValueError('Injected reader failure')
  return self.memory.read(*args)
checks=0
try:
 for row in r['wall_diagnostic_frames']:
  a=ClosedGraph.decode(Path(row['graph']).read_bytes());_,_,m,sources=h.assets.get(a)
  expected=endpoint_road_span_candidates(a,m,sources,table,include_empty=True)
  for fail in (False,True):
   enabled=gc.isenabled();gc.disable()
   try:
    proxy=Proxy(m,fail);ref=weakref.ref(proxy)
    try:actual=endpoint_road_span_candidates(a,proxy,sources,table,include_empty=True)
    except ValueError:
     if not fail:raise
    else:
     assert not fail and actual==expected
    del proxy
    assert ref() is None,'Recursive endpoint visitor retained memory reader'
    checks+=1
   finally:
    if enabled:gc.enable()
finally:h.close()
print('PASS endpoint visitor release and candidate parity',checks,'normal/failure checks')
