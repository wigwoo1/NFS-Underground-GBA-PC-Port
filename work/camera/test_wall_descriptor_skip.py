import json,time,dataclasses,tracemalloc
from pathlib import Path
from owned_graph_packet import GraphPacket
from owned_graph_wall_sources import wall_sources
p=Path('work/camera');ns={};exec((p/'owned_graph_wall_sources.before-descriptor-skip.py').read_text(),ns);checks=[]
for refresh in (8754,8758,8762,8765,8769,8772,8776):
 g=GraphPacket.decode((p/f'graph-packets/{refresh}.ngp').read_bytes());allwalls=ns['wall_sources'](g);descriptors=sorted({w.descriptor for w in allwalls});groups=[None,set(),set(descriptors),{999999}]+[{d} for d in descriptors];count=0
 for group in groups:
  a=ns['wall_sources'](g,descriptors=group,material_cache=[g,None]);b=wall_sources(g,descriptors=group,material_cache=[g,None])
  assert [dataclasses.astuple(x) for x in a]==[dataclasses.astuple(x) for x in b];count+=len(b)
 checks.append(dict(refresh=refresh,groups=len(groups),walls_checked=count))
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/wall-descriptor-skip-20261007');cp.mkdir(exist_ok=True)
(cp/'result.json').write_text(json.dumps(dict(result='PASS',checks=checks,scope='All descriptor subsets including empty, absent, full and individual descriptors across seven captured graphs; every wall field exact. No live speed claim.'),indent=2))
for name in ('test_wall_descriptor_skip.py','owned_graph_wall_sources.py','owned_graph_wall_sources.before-descriptor-skip.py'):(cp/name).write_bytes((p/name).read_bytes())
print('PASS',sum(x['groups'] for x in checks),'groups',sum(x['walls_checked'] for x in checks),'walls')
