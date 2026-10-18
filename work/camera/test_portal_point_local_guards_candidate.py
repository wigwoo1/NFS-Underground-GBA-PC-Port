import json,struct,math
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_portal_traversal import traverse as baseline
from owned_portal_traversal_point_local_candidate import traverse as candidate
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());g=ClosedGraph.decode(Path(r['wall_diagnostic_frames'][0]['graph']).read_bytes()).graph
matrix=struct.unpack_from('<12i',g.context,256);fb=g.context[304:368];root=struct.unpack_from('<8H',g.context,368);table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);graph=dict(g.graph()[0]);camera=tuple(x/16384 if i<9 else float(x) for i,x in enumerate(matrix));checks=[]
cases=[('ordinary',{}),('sampled',{'sampled_camera':camera}),('nan',{'sampled_camera':(math.nan,)*12}),('short_camera',{'sampled_camera':(1.,)}),('capacity',{'capacity':1}),('missing_root',{'graph':{}}),('malformed_ring',{'graph':{root[0]:(b'x',0,159)}})]
for name,changes in cases:
 results=[]
 for fn in (baseline,candidate):
  args=dict(graph=graph,matrix=matrix,framebuffer=fb,root=root,reciprocal=table,descriptor_links=g.descriptor_links);args.update(changes);trace=[]
  try:results.append(('value',fn(**args,diagnostic_trace=trace),trace))
  except (ValueError,KeyError,struct.error) as e:results.append(('error',type(e).__name__,str(e),trace))
 assert results[0]==results[1],(name,results)
 checks.append(dict(case=name,outcome=results[0][0]))
out=dict(result='PASS_LOCAL_PORTAL_GUARD_AND_TRACE_PARITY',checks=checks,scope='Actual graph, exact ordinary/sample traces and rejection outcomes for invalid camera, capacity, absent root and malformed ring. Full route fidelity remains independent.')
Path('work/camera/prototype-runs/portal-point-local-guards.json').write_text(json.dumps(out,indent=2));print(out)
