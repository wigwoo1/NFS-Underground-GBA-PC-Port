"""Verify captured renderer edge outputs and identify source topology changes."""
from pathlib import Path
import ctypes as C,csv,json
p=Path('work/camera');prefix='road-attribute-motion'
edges=list(csv.DictReader((p/(prefix+'-edges.csv')).open()))
sources=list(csv.DictReader((p/(prefix+'-sources.csv')).open()));assert len(sources)==12
lib=C.CDLL(str((p/'road-near-attributes.dll').resolve()))
near=lib.nf_road_near_attributes;near.argtypes=[C.c_double,C.c_double,C.c_void_p,C.c_uint,C.c_uint,C.c_uint,C.c_int,C.c_void_p,C.c_void_p]
recip=(C.c_uint32*32768).from_buffer_copy((p/'road-correction-reciprocal.bin').read_bytes())
frames=[{} for _ in sources];crossings=0;maximum=0
for row in edges:
 index=int(row['index']);key=(int(row['identity']),int(row['edge']))
 assert key not in frames[index];frames[index][key]=row
 z0,z1=float(row['z0']),float(row['z1']);crossing=int(row['crossing']);assert crossing==((z0<64)!=(z1<64))
 if crossing:
  attrs=(C.c_int32*4)(*[int(row[k]) for k in ('a0','a1','b0','b1')]);uv=(C.c_double*2)()
  assert near(z0,z1,attrs,int(row['shift']),int(row['height']),int(row['affine']),64,recip,uv)
  expected=[uv[0]+int(row['offset0'])/(256*(1<<int(row['shift']))),uv[1]+int(row['offset1'])/(256*int(row['height']))]
  error=max(abs(float(row[k])-expected[i]) for i,k in enumerate(('u','v')));maximum=max(maximum,error);assert error<1e-12;crossings+=1
for index,frame in enumerate(frames):
 assert len({int(r['ring']) for r in frame.values()})==int(sources[index]['rings'])
 assert sum(int(r['crossing']) for r in frame.values())==int(sources[index]['near_crossings'])
changes=[];shared=0
for index,(a,b) in enumerate(zip(frames,frames[1:])):
 for key in a.keys()&b.keys():
  shared+=1
  if a[key]['crossing']!=b[key]['crossing']:
   changes.append(dict(frame_pair=[index,index+1],identity=key[0],edge=key[1],before_depths=[float(a[key][k]) for k in ('z0','z1')],after_depths=[float(b[key][k]) for k in ('z0','z1')],before_crossing=int(a[key]['crossing']),after_crossing=int(b[key]['crossing'])))
report=dict(result='PASS',captured_edges=len(edges),corrected_crossings=crossings,shared_source_edge_pairs=shared,topology_changes=changes,maximum_uv_output_difference=maximum,scope='Actual captured corrected edge output matches source-depth UV policy with animation; identifies source-edge clipping changes by exact world-geometry/raw-attribute identity. Hash is diagnostic, not packet identity/security proof. No original GPU pixel parity or transition smoothness proof.')
(p/(prefix+'-edge-tests.json')).write_text(json.dumps(report,indent=2));print(report)
