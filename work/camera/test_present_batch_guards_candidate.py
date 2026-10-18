import ctypes as C,threading,json
from pathlib import Path
p=Path(__file__).parent;d=C.CDLL(str((p/'owned-d3d-present-batch-candidate.dll').resolve()));f=d.nf_d3d_present_batch;f.argtypes=[C.c_void_p,C.c_void_p,C.c_size_t]
a=(C.c_uint64*27)(*[123]*27)
assert f(None,a,C.sizeof(a))==37 and list(a)==[123]*27
assert d.nf_d3d_open()==0
try:
 for ptr,n in ((None,C.sizeof(a)),(a,0),(a,C.sizeof(a)-8),(a,C.sizeof(a)+8)):
  assert f(None,ptr,n)==37 and list(a)==[123]*27
 done=[]
 t=threading.Thread(target=lambda:done.append(f(None,a,C.sizeof(a))));t.start();t.join(1);assert not t.is_alive() and done==[37] and list(a)==[123]*27
 assert f(None,a,C.sizeof(a))==38
 assert d.nf_d3d_close()==0
 assert f(None,a,C.sizeof(a))==37
finally:
 d.nf_d3d_close()
out=dict(result='PASS_NATIVE_PRESENT_BATCH_ARGUMENT_OWNER_LIFECYCLE_GUARDS',rejected=8,scope='Exact output size/null/ownerthread/unopened and closeddevice/wrongwindow guards. No out of bounds writes on rejected arguments; rendering/actualwindow parity covered separately.')
Path('work/camera/prototype-runs/present-batch-guards-20261009.json').write_text(json.dumps(out,indent=2));print(out)
