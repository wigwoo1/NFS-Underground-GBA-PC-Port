from pathlib import Path
import ctypes as C,json
p=Path('work/camera');d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()))
class Source(C.Structure):_fields_=[('region',C.c_uint32),('head',C.c_uint32)]
class Cursor(C.Structure):_fields_=[('current',C.c_uint32),('count',C.c_uint32),('seen',C.c_uint8*512)]
class Collector(C.Structure):_fields_=[('cursor',Cursor),('awaiting_callback',C.c_uint)]
class Dispatch(C.Structure):_fields_=[('sources',Source*512),('count',C.c_uint),('next',C.c_uint),('object_count',C.c_uint),('collector',Collector)]
begin=d.nfs_visibility_object_dispatch_begin;begin.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_uint]
next_source=d.nfs_visibility_object_dispatch_next;next_source.argtypes=[C.c_void_p,C.c_void_p]
step=d.nfs_visibility_object_collect_step;step.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p]
sources=(Source*3)(Source(3,0),Source(4,1),Source(5,0));owner=Dispatch();assert begin(C.byref(owner),sources,3,2);sources[0].head=1
objects=C.create_string_buffer(328);objects[2]=b'\xff';objects[3]=b'\xff';objects[166]=b'\xff';objects[167]=b'\xff'
bits=C.create_string_buffer(32);matrix=(C.c_uint32*12)();head=C.c_uint(65535);maximum=C.c_uint();selector=C.c_uint();region=C.c_uint()
for expected_region,expected_head in ((3,0),(4,1),(5,0)):
 assert next_source(C.byref(owner),C.byref(region))==1 and region.value==expected_region and owner.collector.cursor.current==expected_head
 before=bytes(owner);region.value=999;assert next_source(C.byref(owner),C.byref(region))==-1 and bytes(owner)==before and region.value==999
 assert step(C.byref(owner.collector),objects,bits,32,matrix,C.byref(head),C.byref(maximum),C.byref(selector))==1
assert bits.raw[0]==3 and head.value==65535
before=bytes(owner);assert next_source(C.byref(owner),C.byref(region))==0 and bytes(owner)==before and region.value==999
bad=(Source*1)(Source(512,0));assert not begin(C.byref(owner),bad,1,2) and bytes(owner)==before
bad[0]=Source(1,2);assert not begin(C.byref(owner),bad,1,2) and bytes(owner)==before
report=dict(result='PASS',owned_source_starts=3,pending_rejections=3,atomic_invalid_plans=2,scope='Owned source copying, repeated heads with shared visit bitmap, pending-source rejection and exhausted plan; inactive objects avoid callbacks/sorting.')
(p/'object-dispatch-tests.json').write_text(json.dumps(report,indent=2));print(report)
