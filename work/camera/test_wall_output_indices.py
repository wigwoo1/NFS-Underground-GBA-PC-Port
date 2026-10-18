"""Independent output-index formulas across all source indices/shade levels."""
import ctypes as C,json,runpy
from pathlib import Path
p=Path(__file__).resolve().parent
fixture=runpy.run_path(str(p/'test_wall_write_states.py'))
d=C.CDLL(str(p/'visibility-probe-wide.dll'));P=C.c_void_p;U=C.c_uint32
f=d.nf_wall_output_indices_owned;states=d.nf_wall_write_states_owned
for fn in (f,states):fn.argtypes=[fixture['Reader'],P,U,U,C.POINTER(P)]+[C.POINTER(U)]*3
d.nf_surface_free.argtypes=[P]
checked=0
for flags,planes in ((0,17),(256,1)):
    ptr=P();state=P();w=U();h=U();n=U()
    args=[fixture['read'],None,0x1000,flags]
    assert f(*args,C.byref(ptr),C.byref(w),C.byref(h),C.byref(n))
    assert (w.value,h.value,n.value)==(256,1,planes)
    expected=bytes(range(256))
    if planes==17:expected+=bytes(fixture['table'][index*16+level] if index else 0 for level in range(16) for index in range(256))
    assert C.string_at(ptr,len(expected))==expected
    assert states(*args,C.byref(state),C.byref(w),C.byref(h),C.byref(n))
    classified=C.string_at(state,len(expected))
    for j,index in enumerate(expected):
        source=j%256
        assert classified[j]==(0 if not source else 2 if index else 1)
    saved=fixture['regions'].copy();fixture['regions'].clear()
    assert C.string_at(ptr,len(expected))==expected
    fixture['regions'].update(saved)
    d.nf_surface_free(ptr);d.nf_surface_free(state);checked+=len(expected)
rejects=0
for flags,missing in ((128,None),(0,0x3000),(0,0x4000),(0,0x2000),(256,0x1000)):
    saved=fixture['regions'].pop(missing) if missing else None
    ptr=P(123);w=U(41);h=U(42);n=U(43)
    assert not f(fixture['read'],None,0x1000,flags,C.byref(ptr),C.byref(w),C.byref(h),C.byref(n))
    assert (ptr.value,w.value,h.value,n.value)==(123,41,42,43)
    if missing:fixture['regions'][missing]=saved
    rejects+=1
report=dict(result='PASS',output_indices_exact=checked,classification_consistent=True,atomic_rejections=rejects,
    scope='All256 sourceindices and16 shadelevels synthetic formula/ownership; actual wall table provenance, packet andGPU wiring pending.')
(p/'wall-output-indices-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
