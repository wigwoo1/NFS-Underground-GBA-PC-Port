from pathlib import Path
import struct,json
from owned_closed_graph import ClosedGraph
from owned_closed_supplements import ClosedSupplements
source=Path('work/camera/test_owned_fully_fileless_graph.py').read_text()
source=source.replace('active=False;nonempty=None;', 'supplement_closed=[];active=False;nonempty=None;')
source=source.replace('active=False;nonempty=None;', 'active=False;nonempty=None;')
source=source.replace('d.nf_owned_graph_closed_read.argtypes=', 'd.nf_owned_supplement_closed_read.argtypes=[C.c_uint64,C.c_uint,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)]\nd.nf_owned_graph_closed_read.argtypes=')
source=source.replace('closed.append(out.raw);last=candidate','closed.append(out.raw);last=candidate\n    sn=C.c_size_t();assert d.nf_owned_supplement_closed_read(epoch,candidate,None,0,C.byref(sn));so=C.create_string_buffer(sn.value);assert d.nf_owned_supplement_closed_read(epoch,candidate,so,sn.value,C.byref(sn));supplement_closed.append(so.raw)\n    assert not d.nf_owned_supplement_closed_read(epoch+1,candidate,None,0,C.byref(sn))\n    assert not d.nf_owned_supplement_closed_read(epoch,candidate+1,None,0,C.byref(sn))')
exec(compile(source,'closed_supplement_replay','exec'))
checks=[]
for graph_bytes,supplement_bytes in zip(closed,supplement_closed):
 graph=ClosedGraph.decode(graph_bytes);supp=ClosedSupplements.decode(supplement_bytes,graph);checks.append(dict(refresh=graph.refresh,geometry_bytes=len(supp.geometry),texture_bytes=len(supp.textures)))
assert len(checks)==63 and any(c['geometry_bytes'] for c in checks)
(p/'owned-closed-supplement-last.bin').write_bytes(supplement_closed[-1])
r=dict(result='PASS_ATOMIC_CLOSED_SUPPLEMENTAL_OWNERSHIP',checks=checks,stale_epoch_refresh_rejected=True,original_ram_bytes_exact=294912,scope='Atomic supplemental geometry/texture ownership paired with closed graph; live consumer integration pending.')
(p/'owned-closed-supplements.json').write_text(json.dumps(r,indent=2));print(r['result'],len(checks))
