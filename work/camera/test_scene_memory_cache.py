import runpy,threading
from owned_closed_scene_memory import scene_memory,ClosedSceneMemory,_scene_memory_local
v=runpy.run_path('work/camera/audit_failed_world_motion.py');closed=v['scenes'][0].graph;rom=v['rom'];a=scene_memory(closed,rom);assert scene_memory(closed,rom) is a
assert dict(a.owned)==dict(ClosedSceneMemory(closed,rom).owned)
other=bytes(bytearray(rom));assert scene_memory(closed,other) is not a
result=[]
t=threading.Thread(target=lambda:result.append(scene_memory(closed,rom)));t.start();t.join();assert result[0] is not a and dict(result[0].owned)==dict(a.owned)
for i in range(6):scene_memory(closed,bytes(bytearray(rom)))
assert len(_scene_memory_local.entries)==4
print('PASS exact scene/ROM identity reuse, ROM and thread isolation, bounded4entries and byte parity')
