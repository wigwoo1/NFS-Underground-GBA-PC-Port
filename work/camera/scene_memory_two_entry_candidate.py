"""Isolated two-entry scene-memory retention candidate; no GC policy changes."""
import sys
import owned_closed_scene_memory as memory
original=memory.scene_memory
stats={'calls':0,'trimmed_entries':0}
def bounded(closed,rom):
    result=original(closed,rom)
    entries=getattr(memory._scene_memory_local,'entries',[])
    if len(entries)>2:
        stats['trimmed_entries']+=len(entries)-2
        memory._scene_memory_local.entries=entries[-2:]
    stats['calls']+=1
    return result
def install():
    for module in list(sys.modules.values()):
        if module is None or module.__name__ in (__name__,'__main__'):continue
        for key,value in list(vars(module).items()):
            if value is original:setattr(module,key,bounded)
    memory.scene_memory=bounded
