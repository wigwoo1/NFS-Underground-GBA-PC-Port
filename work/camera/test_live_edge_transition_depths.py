"""Depth-linear diagnostic sweep of identified live source edges; no rigid replay."""
from pathlib import Path
import csv,ctypes as C,json,math,struct
p=Path('work/camera');changes=json.loads((p/'road-attribute-motion-edge-tests.json').read_text())['topology_changes'];assert len(changes)==6
rows=list(csv.DictReader((p/'road-attribute-motion-edges.csv').open()))
bykey={(int(r['index']),int(r['identity']),int(r['edge'])):r for r in rows}
lib=C.CDLL(str((p/'road-near-attributes.dll').resolve()));ref=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()));P=C.c_void_p
near=lib.nf_road_near_attributes;near.argtypes=[C.c_double,C.c_double,P,C.c_uint,C.c_uint,C.c_uint,C.c_int,P,P]
vertex=lib.nf_road_vertex_attributes;vertex.argtypes=[C.c_double,P,C.c_uint,C.c_uint,C.c_uint,P,P]
clip=ref.nfs_visibility_wall_clip;clip.argtypes=[P,P,P,C.c_int,C.c_uint,C.c_uint,P]
project=ref.nfs_visibility_surface_vertices;project.argtypes=[P,P,P,P,P,P,C.c_size_t,P]
recip=(C.c_uint32*32768).from_buffer_copy((p/'road-correction-reciprocal.bin').read_bytes())
def evaluate(z,raw,shift,height,affine):
 out=(C.c_double*2)();assert near(*z,raw,shift,height,affine,64,recip,out);return list(out)
dense=integer=cell=0;results=[]
for change in changes:
 row=bykey[(9,change['identity'],change['edge'])];raw=(C.c_int32*4)(*[int(row[k]) for k in ('a0','a1','b0','b1')]);shift,height,affine=[int(row[k]) for k in ('shift','height','affine')]
 start,end=change['before_depths'],change['after_depths'];moving=next(i for i in range(2) if (start[i]<64)!=(end[i]<64));other=1-moving
 t=(64-start[moving])/(end[moving]-start[moving]);stationary=start[other]+(end[other]-start[other])*t
 for i in range(513):
  z=[start[k]+(end[k]-start[k])*i/512 for k in range(2)]
  if (z[0]<64)!=(z[1]<64):
   assert all(math.isfinite(v) for v in evaluate(z,raw,shift,height,affine));dense+=1
   zs=[math.floor(v) for v in z]
   if (zs[0]<64)!=(zs[1]<64):
    scratch=bytearray(52);struct.pack_into('<2h',scratch,4,*zs);edge=C.create_string_buffer(bytes(scratch));heights=(C.c_uint32*4)();attrs=(C.c_uint32*4)(*[v&0xffffffff for v in raw]);stream=C.create_string_buffer(48);count=C.c_uint()
    assert clip(edge,heights,attrs,64,0,0,recip)==1
    params=(C.c_uint32*6)(1,0,0,shift,height,affine);assert project(edge,heights,attrs,params,recip,stream,48,C.byref(count))
    words=struct.unpack_from('<6i',stream.raw);q=65536 if affine else words[3];expected=[words[4]/q/((1<<shift)*.5),words[5]/q/(height*.5)]
    assert max(abs(a-b) for a,b in zip(evaluate(zs,raw,shift,height,affine),expected))<1e-12;integer+=1
 # Approach clipping boundary on its valid side, recording biased endpoint gap.
 side=-1 if stationary>=64 else 1
 z=[0.,0.];z[other]=stationary;z[moving]=64+side*1e-8
 limit=evaluate(z,raw,shift,height,affine);uv=(C.c_double*2)();corner=(C.c_int32*2)(raw[moving*2],raw[moving*2+1]);assert vertex(64,corner,shift,height,affine,recip,uv)
 gap=max(abs(limit[k]-uv[k]) for k in (0,1))
 # Check fractional extension across each moving-depth integer cell.
 max_cell=0
 for depth in range(math.ceil(min(start[moving],end[moving])),math.floor(max(start[moving],end[moving]))+1):
  if depth==64:continue
  pair=[]
  for sign in (-1,1):
   z[moving]=depth+sign*1e-8
   if (z[0]<64)!=(z[1]<64):pair.append(evaluate(z,raw,shift,height,affine))
  if len(pair)==2:
   error=max(abs(pair[0][k]-pair[1][k]) for k in (0,1));max_cell=max(max_cell,error);assert error<1e-7;cell+=1
 results.append(dict(identity=change['identity'],edge=change['edge'],moving_endpoint=moving,other_endpoint_depth_at_boundary=stationary,boundary_fraction=t,maximum_cell_limit_difference=max_cell,generated_to_uncut_corner_uv_gap=gap,classification='corner-continuous' if gap<1e-6 else 'original-biased-front-boundary-gap'))
report=dict(result='PASS',dense_clipped_samples=dense,original_integer_differentials=integer,depth_cell_limit_checks=cell,edges=results,scope='Captured attributes with linearly swept endpoint depths. Integer clipping/projected UV matches original native reference, previously ARM checked. Continuous depth-cell extension verified; front-on-plane biased-original corner gaps measured explicitly. No actual intermediate rigid poses, GPU raster/pixel continuity or gameplay timing proof.')
(p/'live-edge-transition-depth-tests.json').write_text(json.dumps(report,indent=2));print(report)
