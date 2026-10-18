import dataclasses,json,time
from pathlib import Path
from owned_graph_packet import GraphPacket
from owned_graph_wall_sources import wall_sources
p=Path('work/camera');ns={};exec((p/'owned_graph_wall_sources.before-material-cache.py').read_text(),ns);checks=[]
for refresh in (8754,8758,8762,8765,8769,8772,8776):
 graph=GraphPacket.decode((p/f'graph-packets/{refresh}.ngp').read_bytes());allwalls=ns['wall_sources'](graph);descriptors=sorted({x.descriptor for x in allwalls})[:12];cache=[graph,None];old_ns=new_ns=0;walls=0
 for descriptor in descriptors:
  t=time.perf_counter_ns();a=ns['wall_sources'](graph,descriptors={descriptor});old_ns+=time.perf_counter_ns()-t
  t=time.perf_counter_ns();b=wall_sources(graph,descriptors={descriptor},material_cache=cache);new_ns+=time.perf_counter_ns()-t
  assert [dataclasses.asdict(x) for x in a]==[dataclasses.asdict(x) for x in b];walls+=len(b)
 assert cache[1] is not None
 try:wall_sources(graph,material_cache=[object(),cache[1]])
 except ValueError as e:assert 'owner mismatch' in str(e)
 else:raise AssertionError('Different graph cache accepted')
 checks.append(dict(refresh=refresh,descriptor_calls=len(descriptors),walls=walls,baseline_ms=old_ns/1e6,cached_ms=new_ns/1e6))
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/wall-material-owner-cache-20261007');cp.mkdir(exist_ok=True)
(cp/'result.json').write_text(json.dumps(dict(result='PASS',checks=checks,scope='Seven captured graph owners, descriptor-group wall fields exact and wrong-owner rejection. Single paired CPU wall sample per graph, not controlled live timing.'),indent=2))
for name in ('test_wall_material_owner_cache.py','owned_graph_wall_sources.py','owned_graph_wall_sources.before-material-cache.py','owned_motion_wall_regions.py'):(cp/name).write_bytes((p/name).read_bytes())
print(json.dumps(checks))
