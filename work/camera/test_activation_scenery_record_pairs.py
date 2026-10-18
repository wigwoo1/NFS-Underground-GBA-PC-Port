"""Prepare complete source records on both sides of original slot activation."""
import runpy
from pathlib import Path
from owned_motion_scene import MotionScene
from owned_closed_supplements import ClosedSupplements
from owned_model_builder_inputs import OwnedModelBuilders
from owned_scenery_record_pairs import prepare_scenery_record_pairs
v=runpy.run_path('work/camera/test_inactive_scenery_visits.py');scenes=[]
for i,label in enumerate(('older','newer')):
 graph=v['scenes'][i];supplements=ClosedSupplements.decode((v['folder']/(label+'.supplements.bin')).read_bytes(),graph,v['rom'])
 scenes.append(MotionScene(graph,supplements,OwnedModelBuilders((v['folder']/(label+'.builders.bin')).read_bytes())))
pairs=prepare_scenery_record_pairs(scenes,[v['portal'].sample(i) for i in (0,1)],v['rom'])
assert {p.object_index for p in pairs}=={31,34,37,44,48}
assert all(not p.older_allocated and p.newer_allocated for p in pairs)
assert all(len(p.older_blocks)==len(p.newer_blocks)==12 for p in pairs)
assert all(p.older_blocks[2]!=p.newer_blocks[2] for p in pairs)
assert all(isinstance(block,bytes) for p in pairs for block in p.older_blocks+p.newer_blocks)
print('PASS: five complete immutable candidate record pairs; original slot activation preserved; source poses differ')

# Exercise the optional byte-parity substage trace and prove it is observational.
import owned_scenery_record_pairs as scenery_pairs
fine_trace=[];previous_trace=scenery_pairs._fine_parity_trace
try:
 scenery_pairs._fine_parity_trace=True
 traced=prepare_scenery_record_pairs(scenes,[v['portal'].sample(i) for i in (0,1)],v['rom'],timing=fine_trace)
finally:scenery_pairs._fine_parity_trace=previous_trace
assert traced==pairs
parity_rows=[row for row in fine_trace if row.get('phase')=='exact_topology_material_parity']
assert len(parity_rows)==5
assert all(len(row['checks'])==7 and all(item['equal'] for item in row['checks']) for row in parity_rows)
assert all(item['older_bytes']==item['newer_bytes'] for row in parity_rows for item in row['checks'])
print('PASS: optional exact-byte parity trace preserves all five complete source record pairs')
