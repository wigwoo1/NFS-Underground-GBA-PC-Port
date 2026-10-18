import ctypes as C,gc,json
from pathlib import Path
from types import SimpleNamespace
from owned_source_draw_context_candidate import OwnedSourceDraw
args=dict(frame=bytes(40),camera=(C.c_double*12)(*range(12)),models=(C.c_double*12)(*range(12)),bounds=(C.c_double*4)(1,2,3,4),count=1,a=(C.c_int32*12)(*range(12)),b=(C.c_int32*12)(*range(12)),ra=(C.c_double*12)(*range(12)),rb=(C.c_double*12)(*range(12)),alpha=.5,offsets=(C.c_uint32*2)(0,3),mask=(C.c_uint8*3)(1,0,1),total=3)
owned=OwnedSourceDraw(**args);snapshots=[list(array) for array in owned.owners[1:]]
for key in ('camera','models','bounds','a','b','ra','rb','offsets','mask'):
 for index in range(len(args[key])):args[key][index]=0
sky=SimpleNamespace(lower=bytearray([8])*15136,upper=bytearray([9])*15136,weight=.3);owned.attach_sky(sky);sky.lower[:]=bytes(15136);sky.upper[:]=bytes(15136);del args;gc.collect();assert [list(array) for array in owned.owners[1:10]]==snapshots;assert owned.owners[10].raw[:15136]==bytes([8])*15136 and owned.owners[11].raw[:15136]==bytes([9])*15136
assert C.string_at(owned.context.draw.frame,40)==bytes(40)
root=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/immutable-source-frame-20261007');root.mkdir(exist_ok=True);result=dict(result='PASS_PRIVATE_SOURCE_DRAW_OWNERS',mutable_input_arrays=9,private_sky_planes=2,caller_mutation_and_gc_survived=True,scope='Private data lifetime for native synchronous source draw context; queued publication/cancellation lifecycle remains unverified.');(root/'ownership-tests.json').write_text(json.dumps(result,indent=2));(root/Path(__file__).name).write_text(Path(__file__).read_text());print(json.dumps(result))
