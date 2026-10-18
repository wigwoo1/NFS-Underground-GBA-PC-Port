"""Scalar cache-call ledger, opt-in and bounded; no cache policy changes."""
import sys,collections
import owned_closed_scene_memory as memory
original=memory.scene_memory
calls=hits=0
indices=collections.Counter();rows=[];dropped=0
def traced(closed,rom):
    global calls,hits,dropped
    entries=getattr(memory._scene_memory_local,'entries',[])
    hit=next((i for i,(owner,source,_) in enumerate(entries) if owner is closed and source is rom),None)
    result=original(closed,rom);calls+=1
    if hit is not None:hits+=1;indices[hit]+=1
    row=dict(epoch=closed.epoch,refresh=closed.refresh,hit_index=hit)
    if len(rows)<1024:rows.append(row)
    else:dropped+=1
    return result
def install():
    for module in list(sys.modules.values()):
        if module is None or module.__name__==__name__:continue
        for key,value in list(vars(module).items()):
            if value is original:setattr(module,key,traced)
    memory.scene_memory=traced
def snapshot():
    return dict(calls=calls,hits=hits,hit_indices=dict(indices),rows=list(rows),dropped=dropped,
                scope='Current exact-identity cache calls only, bounded scalar rows; does not change retention.')
