import gc,runpy,json,collections,types,contextlib,io
from pathlib import Path
import owned_wall_visibility_candidate as wall
wall.batch=runpy.run_path('work/camera/owned_wall_visibility_candidate.py.before-type-cache')['batch']
saved=gc.get_debug();gc.collect();assert not gc.garbage
try:
 gc.set_debug(gc.DEBUG_SAVEALL)
 with contextlib.redirect_stdout(io.StringIO()):namespace=runpy.run_path('work/camera/test_precomputed_source_eight_samples.py',run_name='__main__')
 del namespace
 collected=gc.collect();types_count=collections.Counter(type(x).__module__+'.'+type(x).__qualname__ for x in gc.garbage)
 functions=collections.Counter(x.__code__.co_filename+':'+x.__qualname__ for x in gc.garbage if isinstance(x,types.FunctionType))
 ctypes_owned=collections.Counter(type(x).__name__ for x in gc.garbage if type(x).__module__=='ctypes' or hasattr(type(x),'_type_'))
 arrays=collections.Counter((getattr(x,'__module__',''),getattr(x,'__name__',''),getattr(x,'_length_',None),str(getattr(x,'_type_',None))) for x in gc.garbage if isinstance(x,type) and hasattr(x,'_length_'))
 result=dict(array_classes=[dict(module=k[0],name=k[1],length=k[2],element=k[3],count=n) for k,n in arrays.most_common()],result='OBSERVED_UNREACHABLE_OBJECTS',final_collect_count=collected,retained_debug_objects=len(gc.garbage),types=types_count.most_common(30),functions=functions.most_common(30),ctypes_types=ctypes_owned.most_common(20),scope='DEBUG_SAVEALL isolated captured eight-sample workload after deleting run namespace; includes imported/test infrastructure and ctypes ownership cycles. Not live leak or exclusive causality proof.')
finally:
 gc.set_debug(saved);gc.garbage.clear();gc.collect()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/preparation-array-class-owners-20261007');cp.mkdir(exist_ok=True);(cp/'baseline-wall-types.json').write_text(json.dumps(result,indent=2));(cp/Path(__file__).name).write_bytes(Path(__file__).read_bytes());print(json.dumps(result))
