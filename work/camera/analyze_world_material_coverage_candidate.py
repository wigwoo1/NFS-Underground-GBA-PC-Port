"""Conservative submitted-geometry footprint; no pixel fitting or geometry edits."""
import json,hashlib,sys
from pathlib import Path
import numpy as np
folder=Path(sys.argv[1]);m=json.loads((folder/'manifest.json').read_text());rows=[]
for r in m['rows']:
 p=r['world_packets'];assert hashlib.sha256((folder/p['file']).read_bytes()).hexdigest()==p['sha256'];a=np.load(folder/p['file']);v=a['vertices'];offsets=a['offsets'];states=a['states'];coverage=np.zeros((64,3240),bool);draws=[];records=a['texture_records'];rgba=a['texture_rgba']
 for i in range(len(a['texture_ids'])):
  config=np.frombuffer(states[i,:32].tobytes(),'<f4');rect=np.frombuffer(states[i,32:64].tobytes(),'<i4');q=v[offsets[i]:offsets[i+1],:2].astype(np.float64)
  sx=np.float32(2/(float(config[1])-float(config[0])));bx=np.float32(-(float(config[1])+float(config[0]))/(float(config[1])-float(config[0])));sy=np.float32(2/(float(config[3])-float(config[2])));by=np.float32(-(float(config[3])+float(config[2]))/(float(config[3])-float(config[2])))
  clipx=q[:,0]*sx+bx;clipy=q[:,1]*sy+by
  points=np.stack([rect[4]+(clipx+1)*rect[6]/2,2160-rect[5]-rect[7]+(1-clipy)*rect[7]/2],axis=1)
  mask=np.zeros_like(coverage)
  modes=np.frombuffer(states[i,64:].tobytes(),'<u4');sampling=int(modes[0]);w,h,offset,size=map(int,records[int(a['texture_ids'][i])-1]);texture=rgba[offset:offset+size].reshape(h,w,4)
  rejected=0
  for triangle_number,tri in enumerate(points.reshape(-1,3,2)):
   xmin=max(300,int(np.floor(tri[:,0].min()))-1,int(rect[0]));xmax=min(3540,int(np.ceil(tri[:,0].max()))+1,int(rect[2]));ymin=max(r['y'],int(np.floor(tri[:,1].min()))-1,int(rect[1]));ymax=min(r['y']+64,int(np.ceil(tri[:,1].max()))+1,int(rect[3]))
   if xmin>=xmax or ymin>=ymax:continue
   xx=np.arange(xmin,xmax)[None,:]+.5;yy=np.arange(ymin,ymax)[:,None]+.5;edges=[]
   for first,last in zip(tri,np.roll(tri,-1,axis=0)):
    edge=(last[0]-first[0])*(yy-first[1])-(last[1]-first[1])*(xx-first[0]);epsilon=.03*np.linalg.norm(last-first);edges.append((edge,epsilon))
   inside=np.logical_and.reduce([e>=-epsilon for e,epsilon in edges])|np.logical_and.reduce([e<=epsilon for e,epsilon in edges])
   # Affine screen interpolation matches constant vertex clip W=1; UV division is explicit in shader.
   determinant=(tri[1,0]-tri[0,0])*(tri[2,1]-tri[0,1])-(tri[1,1]-tri[0,1])*(tri[2,0]-tri[0,0])
   if abs(determinant)<1e-12:continue
   b1=((xx-tri[0,0])*(tri[2,1]-tri[0,1])-(yy-tri[0,1])*(tri[2,0]-tri[0,0]))/determinant
   b2=((tri[1,0]-tri[0,0])*(yy-tri[0,1])-(tri[1,1]-tri[0,1])*(xx-tri[0,0]))/determinant;b0=1-b1-b2
   attributes=v[offsets[i]+triangle_number*3:offsets[i]+triangle_number*3+3].astype(np.float64)
   u=b0*attributes[0,2]+b1*attributes[1,2]+b2*attributes[2,2];vv=b0*attributes[0,3]+b1*attributes[1,3]+b2*attributes[2,3];divisor=b0*attributes[0,5]+b1*attributes[1,5]+b2*attributes[2,5]
   assert np.all(np.isfinite(divisor)) and np.all(np.abs(divisor)>1e-12)
   tx=u/divisor*w;ty=vv/divisor*h
   ix=np.floor(tx).astype(np.int64);iy=np.floor(ty).astype(np.int64)
   ix=ix%w if sampling&1 else np.clip(ix,0,w-1);iy=iy%h if sampling&2 else np.clip(iy,0,h-1)
   color_alpha=b0*attributes[0,9]+b1*attributes[1,9]+b2*attributes[2,9]
   alpha=color_alpha*(texture[iy,ix,3]/255) if config[4]>0 else color_alpha
   # Keep uncertain triangle and texel boundary pixels; never claim exact D3D edge arithmetic.
   uncertain=np.logical_or.reduce([np.abs(e)<=epsilon for e,epsilon in edges])|(np.abs(tx-np.round(tx))<.001)|(np.abs(ty-np.round(ty))<.001)
   allowed=(alpha>config[6])|uncertain if config[5]>0 else np.ones_like(inside)
   rejected+=int((inside&~allowed).sum());inside&=allowed
   mask[ymin-r['y']:ymax-r['y'],xmin-300:xmax-300]|=inside
  coverage|=mask;draws.append(dict(draw=i,texture_id=int(a['texture_ids'][i]),conservative_pixels=int(mask.sum()),transparent_rejected_pixels=rejected))
 stage=np.frombuffer((folder/r['pixel_file']).read_bytes(),np.uint8).reshape(64,3240,4);world=np.frombuffer((folder/r['world_capture']['pixel_file']).read_bytes(),np.uint8).reshape(64,3240,4);changed=np.any(stage!=world,axis=2)
 rows.append(dict(index=r['index'],y=r['y'],covered_pixels=int(coverage.sum()),changed_pixels=int(changed.sum()),changed_outside_conservative_geometry=int((changed&~coverage).sum()),draws=draws))
out=dict(result='MEASURED_WORLD_MATERIAL_ALPHA_COVERAGE',frames=len(rows),changed_pixels=sum(r['changed_pixels'] for r in rows),changed_outside_conservative_geometry=sum(r['changed_outside_conservative_geometry'] for r in rows),rows=rows,scope='Actual submitted triangles with viewport/scissor and conservative0.03pixel edge band. Material alpha/discard evaluated with conservative triangle and .001texel boundary allowance; remaining footprint upper bound only; no original world visibility proof or screenpolygon matching.')
(folder/'material-coverage-audit.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='rows'})
