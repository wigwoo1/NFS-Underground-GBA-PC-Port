"""Opt-in generation census. Perturbs timing; never cadence evidence."""
import gc,time,types as python_types
from collections import Counter

def snapshot(limit=20):
    if type(limit) is not int or not 1 <= limit <= 64:
        raise ValueError('Invalid census type limit')
    began=time.perf_counter_ns(); generations=[]
    for generation in range(3):
        objects=gc.get_objects(generation); types=Counter(); obj=None
        function_modules=Counter(); project_types=Counter(); view_exporters=Counter()
        view_count=view_bytes=released_views=0
        for obj in objects:
            cls=type(obj);types[cls.__module__+'.'+cls.__qualname__]+=1
            if cls is python_types.FunctionType:
                function_modules[obj.__module__ or '<none>']+=1
            if cls.__module__.startswith(('owned_', 'sample_', 'native_', 'child_')):
                project_types[cls.__module__+'.'+cls.__qualname__]+=1
            if cls is memoryview:
                view_count+=1
                try:
                    exporter_type=type(obj.obj)
                    view_exporters[exporter_type.__module__+'.'+exporter_type.__qualname__]+=1
                    view_bytes+=obj.nbytes
                except ValueError:released_views+=1
        total=len(objects)
        del obj,objects
        generations.append(dict(generation=generation,total=total,
            types=types.most_common(limit),omitted_types=max(0,len(types)-limit),
            function_modules=function_modules.most_common(limit),
            project_types=project_types.most_common(limit),
            views=dict(count=view_count,logical_bytes=view_bytes,released=released_views,
                       exporters=view_exporters.most_common(limit))))
    return dict(generations=generations,elapsed_ns=time.perf_counter_ns()-began,
        scope='Sequential generation snapshots; collector membership may change between scans. Module prefix is classification, not ownership. View logical bytes may overlap and exclude exporter extent. No object references retained or cadence proof.')
