"""Descriptive residual/source-coordinate trace; not a rasterizer or acceptance test."""
from pathlib import Path
import json,numpy as np
p=Path('work/camera/prototype-runs');ops=json.loads((p/'normalized-source-gpu-packets.json').read_text())['ops'];res=json.loads((p/'d3d-matrix-load-residual-pixels.json').read_text());dims={};texture_versions={};payload=(p/'source-command-state-payload.bin').read_bytes();traces=[];current=[];frame=None
for op in ops:
 kind=op['op']
 if kind=='allocate_texture':
  a=op['args'];dims[op['target'][0]]=list(map(int,a[3:5]));w,h=dims[op['target'][0]];start=op['payload_offset'];
  if op['payload_bytes']:texture_versions[tuple(op['target'])]=np.frombuffer(payload[start:start+op['payload_bytes']],np.uint8).reshape(h,w,4)
 if kind=='update_texture':
  key=tuple(op['target']);prev=texture_versions[(key[0],key[1]-1)].copy();a=list(map(int,op['args']));x,y,w,h=a[2:6];start=op['payload_offset'];prev[y:y+h,x:x+w]=np.frombuffer(payload[start:start+op['payload_bytes']],np.uint8).reshape(h,w,4);texture_versions[key]=prev
 if kind=='begin_frame':frame=op['identity'][2];current=[]
 if kind=='draw_triangles' and not op['program']:
  v=np.asarray(op['vertices'],float);l,r,b,t=op['projection'][:4];vx,vy,vw,vh=op['state']['viewport'];pos=np.column_stack((vx+(v[:,0]-l)/(r-l)*vw,2160-vy-(v[:,1]-b)/(t-b)*vh))
  for k in range(0,len(op['indices']),3):
   ids=op['indices'][k:k+3];tri=pos[ids];area=np.cross(tri[1]-tri[0],tri[2]-tri[0]);
   if abs(area)<1e-12:continue
   current.append((op,tri,v[ids],float(area)))
 if kind=='end_frame':
  rows=[]
  for pixel in res[frame]['pixels']:
   pt=np.array([pixel['x']+.5,pixel['y']+.5]);matches=[]
   for op,tri,v,area in current:
    w1=float(np.cross(pt-tri[0],tri[2]-tri[0])/area);w2=float(np.cross(tri[1]-tri[0],pt-tri[0])/area);weights=np.array([1-w1-w2,w1,w2])
    if weights.min()<-0.002:continue
    # Pixel distance to each infinite triangle edge, with coverage margin.
    distances=[abs(float(np.cross(tri[(j+1)%3]-tri[j],pt-tri[j])))/float(np.linalg.norm(tri[(j+1)%3]-tri[j])) for j in range(3)]
    if weights.min()<0 and min(distances)>.02:continue
    tex=op['textures'].get('0');uv_boundary=None;attribution=None
    if tex and tex['resource'][0] in dims:
     q=weights@v[:,2:6]
     if abs(q[3])>1e-12:
      uv=q[:2]/q[3]*dims[tex['resource'][0]];uv_boundary=float(np.min(np.abs(uv-np.round(uv))))
      image=texture_versions.get(tuple(tex['resource']))
      if image is not None:
       ix,iy=np.floor(uv).astype(int);hh,ww=image.shape[:2];neighbors=[]
       for dy in range(-1,2):
        for dx in range(-1,2):
         rgba=image[(iy+dy)%hh,(ix+dx)%ww];neighbors.append(dict(offset=[dx,dy],rgba=rgba.tolist(),gl_match=rgba[:3].tolist()==pixel['gl'],d3d_match=rgba[:3].tolist()==pixel['d3d']))
       attribution=dict(texel=uv.tolist(),resource=tex['resource'],neighbor_texels=neighbors)

    matches.append(dict(source_command=op['source_command'],minimum_edge_distance_pixels=min(distances),minimum_texel_boundary_distance=uv_boundary,inside_continuous_triangle=bool(weights.min()>=0),texture_attribution=attribution))
   rows.append(dict(x=pixel['x'],y=pixel['y'],candidates=matches))
  traces.append(dict(frame=frame,pixels=rows))
r=dict(scope='Continuous double source-coordinate diagnostics, not hardware coverage. Transparent/occluded candidates retained; no definitive visible-draw attribution.',frames=traces)
(p/'d3d-residual-material-traces.json').write_text(json.dumps(r,indent=2))
for f in traces:
 near_edge=sum(any(c['minimum_edge_distance_pixels']<.01 for c in x['candidates']) for x in f['pixels']);near_uv=sum(any(c['minimum_texel_boundary_distance'] is not None and c['minimum_texel_boundary_distance']<.0001 for c in x['candidates']) for x in f['pixels']);same_material=sum(any(c['texture_attribution'] and any(t['gl_match'] for t in c['texture_attribution']['neighbor_texels']) and any(t['d3d_match'] for t in c['texture_attribution']['neighbor_texels']) for c in x['candidates']) for x in f['pixels']);print(dict(frame=f['frame'],pixels=len(f['pixels']),same_material_neighbor_colors=same_material,near_any_triangle_edge=near_edge,near_any_texel_boundary=near_uv))
