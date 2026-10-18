"""Pair-local endpoint object index; preserves duplicate population guards."""
import inspect

def indexed_endpoints(pair,object_index):
    endpoints=pair._ordinary_visit_cache
    cache=getattr(pair,'_indexed_ordinary_endpoints',None)
    if cache is None or cache[0] is not endpoints:
        indexes=[]
        for visits in endpoints:
            index={}
            for visit in visits:index.setdefault(visit['object'],[]).append(visit)
            indexes.append({key:tuple(rows) for key,rows in index.items()})
        cache=(endpoints,tuple(indexes));pair._indexed_ordinary_endpoints=cache
    return tuple(index.get(object_index,()) for index in cache[1])

def install():
    import owned_sampled_model_visit as visits
    import owned_sampled_world_segmented_candidate as world
    if getattr(visits,'indexed_endpoints_selected',False):return
    original=visits.sampled_model_visit
    if world.sampled_model_visit is not original:raise RuntimeError('Unexpected sampled visit binding')
    source=inspect.getsource(original)
    marker="if object_index is not None:endpoint_visits=tuple(tuple(v for v in visits if v['object']==object_index) for visits in endpoint_visits)"
    if source.count(marker)!=1:raise RuntimeError('Unexpected endpoint selection source')
    source=source.replace(marker,'if object_index is not None:endpoint_visits=indexed_endpoints(pair,object_index)')
    namespace=dict(original.__globals__,indexed_endpoints=indexed_endpoints)
    exec(compile(source,'indexed-model-endpoint-visits','exec'),namespace)
    visits.sampled_model_visit=world.sampled_model_visit=namespace['sampled_model_visit']
    visits.indexed_endpoints_selected=True
