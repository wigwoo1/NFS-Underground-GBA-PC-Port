import json,struct,ctypes as C
from dataclasses import replace
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_closed_scene_memory import ClosedSceneMemory
from owned_complete_road_candidates import road_candidates
from owned_complete_road_gpu import encode_road
from owned_endpoint_road_planner import EndpointRoadPlanner
from owned_motion_pairs import records
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());d=C.CDLL(str(Path('work/camera/owned-world-gpu.dll').resolve()));d.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t];d.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t];rgb=C.create_string_buffer(3840*2160*3);checks=[]
def frame_with(frame,geometry):
 h=list(struct.unpack_from('<6I2Q',frame));tail=frame[40+h[2]:];g=b''.join(geometry);h[2]=len(g);return struct.pack('<6I2Q',*h)+g+tail
def encode(row):return struct.pack('<4I',0x3147534e,row['kind'],row['context'],12)+b''.join(struct.pack('<I',len(b))+bytes(b) for b in row['blocks'])
table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);planner=EndpointRoadPlanner(rom,table)
try:
 for f in r['wall_diagnostic_frames']:
  c=ClosedGraph.decode(Path(f['graph']).read_bytes());cs=road_candidates(c,ClosedSceneMemory(c,rom));base=Path(f['regenerated']).read_bytes();roads=[x for x in records(base)['records'] if x['kind']==1];generated=[]
  selected,details=planner.plan(c);generated=[x['record'] for x in selected]
  assert [x['source'].vertices for x in selected]==[bytes(x['blocks'][0]) for x in roads]
  try:planner.plan(c)
  except ValueError:pass
  else:raise AssertionError('Repeated scene accepted')
  reference=frame_with(base,[encode(x) for x in roads]);frame=frame_with(base,generated)
  assert d.nf_owned_gpu_draw(reference,len(reference))==0 and d.nf_owned_gpu_read(rgb,len(rgb))==0;expected=rgb.raw
  assert d.nf_owned_gpu_draw(frame,len(frame))==0 and d.nf_owned_gpu_read(rgb,len(rgb))==0
  assert rgb.raw==expected,(c.refresh,sum(a!=b for a,b in zip(rgb.raw,expected)))
  checks.append(dict(refresh=c.refresh,roads=len(roads),pixels_exact=3840*2160))
finally:planner.close();assert d.nf_owned_gpu_close()
out=dict(result='PASS_INDEPENDENT_ENDPOINT_ROAD_GPU',checks=checks,scope='Raw source road-only 4K parity using independently reconstructed endpoint submission/order/bounds with persistent scratch; sampled selection pending')
Path('work/camera/independent-endpoint-road-gpu-tests.json').write_text(json.dumps(out,indent=2));print(out['result'],len(checks))
