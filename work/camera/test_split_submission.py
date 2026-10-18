"""Real two-scene boundary ownership and queue retirement without a live bridge."""
from pathlib import Path
import ctypes as C,struct,json
p=Path('work/camera');P=C.c_void_p;U=C.c_uint32;Z=C.c_size_t
root=max((p/'prototype-runs').glob('scene-boundary-ownership-*-boundary-hud.bin'),key=lambda q:q.stat().st_mtime);prefix=Path(str(root).removesuffix('-boundary-hud.bin'));hud=root.read_bytes()
d=C.CDLL(str((p/'split-submission.dll').resolve()))
class Time(C.Structure):_fields_=[('epoch',C.c_uint64),('older',C.c_uint64),('newer',C.c_uint64),('alpha',C.c_double),('target',C.c_double)]
class Schedule(C.Structure):_fields_=[('origin',C.c_uint64),('lag',C.c_uint64),('base',U),('delay',C.c_double)]
Read=C.CFUNCTYPE(C.c_int,P,C.c_uint64,U,U,P)
@Read
def read(ctx,e,r,y,out):
 if e!=2 or r!=3524:return 0
 C.memmove(out,hud[y*34944:(y+1)*34944],34944);return 1
zero=(C.c_uint16*160)(*[struct.unpack_from('<H',hud,y*34944+128+32768)[0] for y in range(160)])
d.nf_submission_create.argtypes=[P,Z,C.POINTER(Time),U,U,P,P,Read,P,C.POINTER(P)]
d.nf_submission_schedule_set.argtypes=[P,C.POINTER(Schedule)];d.nf_submission_command_cameras_set.argtypes=[P,P,U];d.nf_submission_destroy.argtypes=[P]
d.nf_render_submission_split.argtypes=[C.POINTER(P),C.POINTER(P),U,C.POINTER(P)];d.nf_render_submission_split_view.argtypes=[P,C.POINTER(P),C.POINTER(P),C.POINTER(U)]
d.nf_render_submission_destroy.argtypes=[P];d.nf_submission_packet.argtypes=[P,C.POINTER(P),C.POINTER(Z)]
d.nf_render_handoff_create.argtypes=[C.c_uint64];d.nf_render_handoff_create.restype=P;d.nf_render_handoff_push.argtypes=[P,C.POINTER(P)];d.nf_render_handoff_pop.argtypes=[P];d.nf_render_handoff_pop.restype=P;d.nf_render_handoff_invalidate.argtypes=[P];d.nf_render_handoff_destroy.argtypes=[P]
packets=[];expected_cameras=[];sources=[]
for label,serial,end in [('older',20,3519),('newer',21,3524)]:
 packet=Path(str(prefix)+'-'+label+'-packet.bin').read_bytes();poses=Path(str(prefix)+'-'+label+'-cameras.bin').read_bytes();packets.append(packet);expected_cameras.append(poses)
 buf=C.create_string_buffer(packet);camera=C.create_string_buffer(poses);out=P();time=Time(2,serial,serial,0,3524.641209083314);assert d.nf_submission_create(buf,len(packet),C.byref(time),end,end,None,zero,read,None,C.byref(out));assert d.nf_submission_command_cameras_set(out,camera,len(poses)//56);assert d.nf_submission_schedule_set(out,C.byref(Schedule(1000,16666667,3454,8)))
 C.memset(buf,165,len(packet));C.memset(camera,165,len(poses));sources.append(out)
a,b=sources;av,bv=a.value,b.value
for row in [0,160,999]:
 sentinel=P(123);assert not d.nf_render_submission_split(C.byref(a),C.byref(b),row,C.byref(sentinel)) and (a.value,b.value,sentinel.value)==(av,bv,123)
sentinel=P(123);assert not d.nf_render_submission_split(C.byref(b),C.byref(a),20,C.byref(sentinel)) and sentinel.value==123
assert not d.nf_render_submission_split(C.byref(a),C.byref(a),20,C.byref(sentinel))
frame=P();assert d.nf_render_submission_split(C.byref(a),C.byref(b),20,C.byref(frame)) and not a.value and not b.value
queue=d.nf_render_handoff_create(2);assert queue and d.nf_render_handoff_push(queue,C.byref(frame)) and not frame.value
popped=d.nf_render_handoff_pop(queue);assert popped
x=P();y=P();row=U();assert d.nf_render_submission_split_view(popped,C.byref(x),C.byref(y),C.byref(row)) and row.value==20
d.nf_submission_command_cameras.argtypes=[P,C.POINTER(P),C.POINTER(U)]
for item,expected,poses in zip([x,y],packets,expected_cameras):
 data=P();size=Z();assert d.nf_submission_packet(item,C.byref(data),C.byref(size)) and C.string_at(data,size.value)==expected
 data=P();count=U();assert d.nf_submission_command_cameras(item,C.byref(data),C.byref(count)) and C.string_at(data,count.value*56)==poses
assert d.nf_render_submission_split_view(popped,C.byref(x),C.byref(y),C.byref(row))
d.nf_render_handoff_invalidate(queue);d.nf_render_submission_destroy(popped);d.nf_render_handoff_destroy(queue)
report=dict(result='PASS',actual_scene_serials=[20,21],split=20,packets_independently_owned=True,negative_atomic_cases=5,queue_transfer_and_popped_retirement=True,scope='Immutable transport only; no mixed-scene GPU clipping or fullscene60fps claim.')
(p/'split-submission-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
