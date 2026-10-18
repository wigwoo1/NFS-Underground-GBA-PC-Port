import sys,time,statistics,json
from pathlib import Path
sys.argv=['fixture','work/camera/prototype-runs/child-scene-1791637661169682300']
setup=Path('work/camera/test_geometry_process_codec_component.py').read_text().split('from owned_progressive_source_samples_candidate import')[0]
exec(compile(setup,'captured_geometry_pack_setup','exec'))
history.close()
from owned_scene_process_transport import pack,unpack
from owned_geometry_process_codec_candidate import pack_geometry
rows={False:[],True:[]};sizes={}
for iteration in range(12):
 for enabled in ((False,True) if iteration%2==0 else (True,False)):
  begin=time.perf_counter_ns();packets=tuple((pack_geometry if enabled else pack)(f,s) for f,s in zip(frames,scenes));end=time.perf_counter_ns()
  sizes[enabled]=sum(len(v) for packet in packets for v in packet if v is not None)
  decoded=tuple(unpack(packet,rom) for packet in packets)
  for key,(frame,scene) in enumerate(decoded):
   assert scene.identity==scenes[key].identity
   assert frame==packets[key][0]
  rows[enabled].append((end-begin)/1e6)
out=dict(result='GEOMETRY_REQUEST_PACK_COST',rounds=12,variants=[dict(selected=e,median_pack_ms=statistics.median(rows[e]),request_bytes=sizes[e]) for e in (False,True)],scope='Captured pair alternating parent pack cost only; excludes transport, child work and frame cadence.')
Path('outputs/nfsug-native-renderer/camera-research/checkpoints/all-successful-native-starvation-20261010/geometry-pack-cost.json').write_text(json.dumps(out,indent=2));print(out)
