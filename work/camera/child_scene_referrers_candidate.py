"""Bounded scalar-only scene referrer diagnostic; never cadence evidence."""
import gc,time,types

def describe(target, ref):
    cls=type(ref);row={'type':cls.__module__+'.'+cls.__qualname__}
    if cls is dict:
        row['direct_keys']=[k for k,v in ref.items() if isinstance(k,str) and v is target][:8]
    elif cls is types.CellType:row['closure_cell']=True
    elif cls is list:row['list_length']=len(ref)
    elif cls is tuple:row['tuple_length']=len(ref)
    return row

def snapshot(limit=12):
    began=time.perf_counter_ns();objects=gc.get_objects()
    names={'owned_closed_scene_memory.ClosedSceneMemory','owned_closed_graph.ClosedGraph','owned_graph_packet.GraphPacket'}
    targets=[o for o in objects if type(o).__module__+'.'+type(o).__qualname__ in names]
    rows=[];selected=targets[:limit]
    for target in selected:
        refs=gc.get_referrers(target)
        rows.append(dict(type=type(target).__module__+'.'+type(target).__qualname__,
            referrers=[describe(target,ref) for ref in refs if ref is not objects and ref is not targets and ref is not selected][:16],
            total_referrers=len(refs)))
        del refs
    return dict(target_count=len(targets),rows=rows,truncated=len(targets)>limit,
                elapsed_ns=time.perf_counter_ns()-began,
                scope='Direct referrers only; diagnostic lists excluded. No ownership, reachability, leak, or cadence proof; scalar results retain no targets.')
