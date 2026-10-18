"""Original replay with only fileless graph APIs enabled; trace writers stay closed."""
from pathlib import Path
import ctypes as C,struct,json
setup=Path('work/camera/capture_motion_scanline_state.py').read_text().split('gpu=None;gpu_worker=None;gpu_checks=[]')[0]
exec(compile(setup,'capture_setup','exec'))
for key in list(os.environ):
 if key.startswith('NF_'):os.environ.pop(key,None);assert crt._putenv((key+'=').encode())==0
os.environ['NF_TEST_RACING_OWNED_CAPTURE']='1';assert crt._putenv(b'NF_TEST_RACING_OWNED_CAPTURE=1')==0
assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(state).encode(),0)
for name in ('read','material_read','objects_read','callbacks_read','associations_read'):
 getattr(d,'nf_owned_graph_live_'+name).argtypes=[C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)]
def read(name):
 f=getattr(d,'nf_owned_graph_live_'+name);n=C.c_size_t();assert f(None,0,C.byref(n));out=C.create_string_buffer(max(1,n.value));assert f(out,n.value,C.byref(n));return out.raw[:n.value]
assert d.nf_native_scene_sink(text_scene_sink,None)
assert d.nf_world_trace(b'')
d.nf_frame.restype=None
d.nf_owned_graph_closed_read.argtypes=[C.c_uint64,C.c_uint,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)]
active=False;nonempty=None;closed=[];last=0
try:
 for row in rows:
  if not active and d.nf_native_scene_refresh()>=8754:assert d.nf_owned_graph_live_enable(1);active=True
  d.nf_frame(int(row['keys']))
  if active:
   candidate=d.nf_owned_graph_closed_latest()
   if candidate and candidate!=last:
    n=C.c_size_t();epoch=d.nf_native_scene_epoch();assert d.nf_owned_graph_closed_read(epoch,candidate,None,0,C.byref(n));out=C.create_string_buffer(n.value);assert d.nf_owned_graph_closed_read(epoch,candidate,out,n.value,C.byref(n));closed.append(out.raw);last=candidate
    assert not d.nf_owned_graph_closed_read(epoch+1,candidate,None,0,C.byref(n))
   cb=read('callbacks_read')
   if cb:nonempty=(cb,read('associations_read'))
 graph=read('read');materials=read('material_read');objects=read('objects_read')
 assert graph==(p/'owned-live-graph-snapshot.bin').read_bytes()
 assert materials==(p/'owned-live-graph-materials.bin').read_bytes()
 assert objects==(p/'owned-live-graph-objects.bin').read_bytes()
 assert nonempty and nonempty[0]==(p/'owned-live-callbacks-nonempty.bin').read_bytes() and nonempty[1]==(p/'owned-live-associations-nonempty.bin').read_bytes()
 for name,address,n in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
  file=p/f'fileless-graph-{name}.bin';d.nf_dump(str(file).encode(),address,n);assert file.read_bytes()==Path(str(source)+'-'+name+'.bin').read_bytes()
finally:d.nf_owned_graph_live_enable(0);d.nf_world_trace(None);d.nf_close()
assert all(hashlib.sha256(Path(x).read_bytes()).hexdigest()==v for x,v in protected.items())
assert closed
assert len({struct.unpack_from('<I',raw,44)[0] for raw in closed})==len(closed)
for raw in closed:
 h=struct.unpack_from('<8I',raw);assert h[:2]==(0x3143474e,1) and sum(h[3:])+40==len(raw)
 assert struct.unpack_from('<I',raw,44)[0]<=h[2]
(p/'owned-closed-graph-last.bin').write_bytes(closed[-1])
r=dict(closed_snapshots=len(closed),closed_refreshes=[struct.unpack_from('<I',x,8)[0] for x in closed],result='PASS_FULLY_FILELESS_GRAPH_OWNERSHIP',diagnostic_writers_enabled=False,graph_bytes=len(graph),material_bytes=len(materials),object_bytes=len(objects),callback_records=len(nonempty[0])//244,association_records=len(nonempty[1])//400,original_ram_bytes_exact=294912,scope='Live raw ownership independent of diagnostic traces; atomic pageflip closure and GPU integration pending.')
(p/'owned-fully-fileless-graph.json').write_text(json.dumps(r,indent=2));print(r)
