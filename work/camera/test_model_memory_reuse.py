import runpy,time
import owned_model_record_builder as module
from owned_scenery_record_pairs import prepare_scenery_record_pairs
v=runpy.run_path('work/camera/test_activation_scenery_record_pairs.py');original=module.ClosedSceneMemory;calls=[]
def counted(closed,rom):
 calls.append(closed);return original(closed,rom)
module.ClosedSceneMemory=counted
try:
 scenes=v['scenes'];queues=[v['v']['portal'].sample(i) for i in (0,1)]
 start=time.perf_counter();pairs=prepare_scenery_record_pairs(scenes,queues,v['v']['rom'],{37,48,44,31,34});elapsed=time.perf_counter()-start
 assert len(pairs)==5 and len(calls)==2 and calls[0] is scenes[0].graph and calls[1] is scenes[1].graph,(len(pairs),len(calls))
 expected={r.object_index:r for r in v['pairs']}
 assert all(r==expected[r.object_index] for r in pairs)
 print('PASS five complete model pairs byte-identical, exactly two identity-owned memory closures',round(elapsed*1000,3),'ms')
finally:module.ClosedSceneMemory=original
