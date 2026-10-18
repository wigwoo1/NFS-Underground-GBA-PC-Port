import ctypes as C,json,runpy
from pathlib import Path
p=Path(__file__).resolve().parent;ns=runpy.run_path(str(p/'test_wall_packet_states.py'));d=ns['d'];P=ns['P'];Z=ns['Z'];U=ns['U'];Section=ns['Section']
attach=d.nf_scene_world_attach_wall_indices;attach.argtypes=[Section,U,P,P,Z,U,C.POINTER(P),C.POINTER(Z)]
borrow=d.nf_scene_world_wall_indices;borrow.argtypes=[Section,U,C.POINTER(P),C.POINTER(P),C.POINTER(Z),C.POINTER(U)]
checked=0;rejects=0
for planes in (1,17):
    states=ns['states'][:planes*4];indices=bytes(77 if s==2 else 0 for s in states)
    raw=C.create_string_buffer(ns['tagged']);a=C.create_string_buffer(states);b=C.create_string_buffer(indices);out=P();size=Z()
    assert attach(Section(C.addressof(raw),len(ns['tagged'])),1,a,b,len(states),planes,C.byref(out),C.byref(size))
    try:tagged=C.string_at(out,size.value)
    finally:d.nf_scene_packet_free(out)
    a.raw=b'\xff'*len(a.raw);b.raw=b'\xff'*len(b.raw)
    packet=C.create_string_buffer(tagged);s=P();i=P();n=Z();levels=U()
    assert borrow(Section(C.addressof(packet),len(tagged)),1,C.byref(s),C.byref(i),C.byref(n),C.byref(levels))
    assert (n.value,levels.value)==(len(states),planes) and C.string_at(s,n.value)==states and C.string_at(i,n.value)==indices
    ns['valid'](ns['packet'](tagged,ns['lighting'] if planes==17 else ns['unlit']),True)
    ns['valid'](ns['packet'](tagged,ns['unlit'] if planes==17 else ns['lighting']),False)
    checked+=len(states)*2;rejects+=1
    for broken in (bytes([1])+indices[1:],indices[:1]+bytes([0])+indices[2:]):
        payload=C.create_string_buffer(broken);out=P(123);size=Z(456)
        assert not attach(Section(C.addressof(raw),len(ns['tagged'])),1,states,payload,len(states),planes,C.byref(out),C.byref(size))
        assert (out.value,size.value)==(123,456);rejects+=1
    bad=C.create_string_buffer(tagged[:-1]);s=P(123);i=P(234);n=Z(345);levels=U(456)
    assert not borrow(Section(C.addressof(bad),len(tagged)-1),1,C.byref(s),C.byref(i),C.byref(n),C.byref(levels))
    assert (s.value,i.value,n.value,levels.value)==(123,234,345,456);rejects+=1
report=dict(result='PASS',paired_bytes_exact=checked,whole_packet_modes=2,atomic_rejections=rejects,
    scope='Modes7/8 owned wall classification/outputindex transport andlighting consistency; assembler/liveGPU consumer notyetwired.')
(p/'wall-packet-indices-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
