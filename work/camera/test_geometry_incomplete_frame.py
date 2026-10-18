from pathlib import Path
import ctypes as C,json
p=Path('work/camera');d=C.CDLL(str((p/'geometry-source-tests.dll').resolve()));d.nf_geometry_sources_append.argtypes=[C.c_uint,C.c_uint,C.c_void_p,C.c_void_p,C.c_uint];d.nf_geometry_sources_read.argtypes=[C.c_uint,C.c_void_p,C.c_size_t,C.c_void_p]
block=C.create_string_buffer(b'raw');blocks=(C.c_void_p*12)(*[C.addressof(block)]*12);sizes=(C.c_uint*12)(*[3]*12)
d.nf_geometry_sources_reset();assert d.nf_geometry_sources_append(1,100,blocks,sizes,12)
# Reject before reading oversized claimed data, and never publish a partial scene.
huge=(C.c_uint*12)(*[700000]*12);assert not d.nf_geometry_sources_append(2,101,blocks,huge,12)
assert not d.nf_geometry_sources_close(10)
out=C.create_string_buffer(b'unchanged',128);before=out.raw;n=C.c_size_t(777)
assert not d.nf_geometry_sources_read(10,out,len(out),C.byref(n));assert out.raw==before and n.value==777
# Failure applies only to the current scene; the next scene recovers normally.
assert d.nf_geometry_sources_append(1,100,blocks,sizes,12);assert d.nf_geometry_sources_close(11)
assert d.nf_geometry_sources_read(11,None,0,C.byref(n));assert n.value==100
assert not d.nf_geometry_sources_append(3,102,blocks,sizes,11);assert not d.nf_geometry_sources_close(12)
assert d.nf_geometry_sources_read(11,None,0,C.byref(n));assert n.value==100
d.nf_geometry_sources_reset();r=dict(result='PASS_INCOMPLETE_GEOMETRY_FRAME_REJECTION',overflow_rejects_partial_frame=True,failed_read_atomic=True,next_scene_recovers=True,prior_complete_scene_retained=True);(p/'geometry-incomplete-frame-tests.json').write_text(json.dumps(r,indent=2));print(r)
