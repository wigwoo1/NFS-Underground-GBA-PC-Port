"""Wide research ABI boundary/atomicity and mismatched consumer rejection."""
from pathlib import Path
import ctypes as C,json,subprocess
p=Path('work/camera').resolve();d=C.CDLL(str(p/'visibility-probe-wide.dll'));assert d.nfs_visibility_queue_capacity()==32
insert=d.nfs_visibility_insert;insert.argtypes=[C.c_void_p,C.c_uint,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p]
for index in (19,20,21,31,32):
 g=C.create_string_buffer(4096);n=C.c_uint32(index);t=C.c_uint32(index)
 ok=insert(g,512,86,32,C.byref(n),C.byref(t));assert bool(ok)==(index<32)
 if ok:assert n.value==t.value==index+1 and g.raw[86*8:86*8+2]==bytes((1,index))
 else:assert n.value==t.value==index and g.raw==bytes(4096)
merge=d.nfs_visibility_merge;merge.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint]
q=C.create_string_buffer(512);g=C.create_string_buffer(4096)
assert merge(q,32,g,512);before=q.raw
assert not merge(q,33,g,512) and q.raw==before
schedule=d.nf_root_region_schedule;schedule.argtypes=[C.c_void_p,C.c_uint,C.c_void_p]
out=C.create_string_buffer(4+32*48);assert schedule(q,32,out)
assert int.from_bytes(out.raw[:4],'little')==64
saved=out.raw;assert not schedule(q,33,out) and out.raw==saved
# Reject incompatible DLL before opening ROM/state or allocating render buffers.
run=subprocess.run([str(p/'live-ordered-preview-wide.exe'),str(p/'visibility-probe.dll'),'missing-rom','missing-state','unused.csv','unused','--sampled-clips'],capture_output=True,text=True)
assert run.returncode==11 and 'visibility capacity mismatch' in run.stderr
report=dict(result='PASS',capacity=32,insertion_cases=5,merge_boundary_atomic=True,root_schedule_boundary_atomic=True,mismatched_consumer_rejected=True,scope='Research ABI boundaries; no gameplay timing proof.')
(p/'visibility-wide-boundary-tests.json').write_text(json.dumps(report,indent=2));print(report)
