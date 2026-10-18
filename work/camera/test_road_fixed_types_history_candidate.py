import sys,json,ctypes as C
from pathlib import Path
from owned_road_record_diagnostic import decode
from owned_road_history_diagnostic import restore,snapshot
sys.argv=['test','work/camera/prototype-runs/owned-native-1791434872973979000.json']
setup=Path('work/camera/test_owned_native_source_backdrop_batch_parity_candidate.py').read_text().split('session=None;results=[]')[0];exec(compile(setup,'actual-road-fixture','exec'))
import owned_endpoint_road_planner as module
from owned_endpoint_road_selection_reuse_candidate import endpoint_road_span_candidates as original
from owned_endpoint_road_fixed_types_candidate import endpoint_road_span_candidates as candidate,private_state,Edges,Stream
for data in (b'',b'abc',bytes(range(256))):assert private_state(data).raw==C.create_string_buffer(data,256).raw
try:private_state(bytes(257))
except ValueError:pass
else:raise AssertionError('Oversize state accepted')
a=private_state(b'x');b=private_state(b'x');a[0]=b'y';assert b.raw[0:1]==b'x'
x=Edges();y=Edges();x[0]=b'z';assert y.raw==bytes(1664)
x=Stream();y=Stream();x[0]=b'z';assert y.raw==bytes(1536)
outputs=[]
try:
 for fn in (original,candidate):
  module.endpoint_road_span_candidates=fn;copy=history.fork()
  try:
   rows,details=copy.plan(scenes[1].graph)
   outputs.append(([(r['descriptor'],r['secondary'],tuple(r['bounds']),r['record'],r['runs']) for r in rows],details,snapshot(copy.scratch)))
  finally:copy.close()
 assert outputs[0]==outputs[1],'Native road records/details/history differ'
finally:module.endpoint_road_span_candidates=original;history.close()
out=dict(result='PASS_CAPTURED_ROAD_SELECTION_NATIVE_HISTORY_PRIVATE_BUFFERS',roads=len(outputs[0][0]),details=len(outputs[0][1]),private_state_edge_stream_isolation=True,short_state_zero_padding=True,oversize_state_rejected=True,scope='Actual captured newer endpoint from identical cloned older road histories; records/details/native scratch exact. One captured endpoint, queued five4K images separately; not route-wide fidelity or live cadence.')
Path('work/camera/prototype-runs/road-fixed-types-history-20261009.json').write_text(json.dumps(out,indent=2));print(out)
