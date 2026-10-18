"""Conservative submitted-geometry footprint; no pixel fitting or geometry edits."""
import json,hashlib
from pathlib import Path
import numpy as np
folder=Path('work/camera/prototype-runs/owned-sky-world-packets-1791590492879412500');m=json.loads((folder/'manifest.json').read_text());rows=[]
for r in m['rows']:
 p=r['world_packets'];assert hashlib.sha256((folder/p['file']).read_bytes()).hexdigest()==p['sha256'];a=np.load(folder/p['file']);v=a['vertices'];offsets=a['offsets'];states=a['states'];coverage=np.zeros((64,3240),bool);draws=[]
 for i in range(len(a['texture_ids'])):
  config=np.frombuffer(states[i,:32].tobytes(),'<f4');rect=np.frombuffer(states[i,32:64].tobytes(),'<i4');q=v[offsets[i]:offsets[i+1],:2].astype(np.float64)
  sx=np.float32(2/(float(config[1])-float(config[0])));bx=np.float32(-(float(config[1])+float(config[0]))/(float(config[1])-float(config[0])));sy=np.float32(2/(float(config[3])-float(config[2])));by=np.float32(-(float(config[3])+float(config[2]))/(float(config[3])-float(config[2])))
  clipx=q[:,0]*sx+bx;clipy=q[:,1]*sy+by
  points=np.stack([rect[4]+(clipx+1)*rect[6]/2,2160-rect[5]-rect[7]+(1-clipy)*rect[7]/2],axis=1)
  mask=np.zeros_like(coverage)
  for tri in points.reshape(-1,3,2):
   xmin=max(300,int(np.floor(tri[:,0].min()))-1,int(rect[0]));xmax=min(3540,int(np.ceil(tri[:,0].max()))+1,int(rect[2]));ymin=max(r['y'],int(np.floor(tri[:,1].min()))-1,int(rect[1]));ymax=min(r['y']+64,int(np.ceil(tri[:,1].max()))+1,int(rect[3]))
   if xmin>=xmax or ymin>=ymax:continue
   xx=np.arange(xmin,xmax)[None,:]+.5;yy=np.arange(ymin,ymax)[:,None]+.5;edges=[]
   for first,last in zip(tri,np.roll(tri,-1,axis=0)):
    edge=(last[0]-first[0])*(yy-first[1])-(last[1]-first[1])*(xx-first[0]);epsilon=.03*np.linalg.norm(last-first);edges.append((edge,epsilon))
   inside=np.logical_and.reduce([e>=-epsilon for e,epsilon in edges])|np.logical_and.reduce([e<=epsilon for e,epsilon in edges]);mask[ymin-r['y']:ymax-r['y'],xmin-300:xmax-300]|=inside
  coverage|=mask;draws.append(dict(draw=i,texture_id=int(a['texture_ids'][i]),conservative_pixels=int(mask.sum())))
 stage=np.frombuffer((folder/r['pixel_file']).read_bytes(),np.uint8).reshape(64,3240,4);world=np.frombuffer((folder/r['world_capture']['pixel_file']).read_bytes(),np.uint8).reshape(64,3240,4);changed=np.any(stage!=world,axis=2)
 rows.append(dict(index=r['index'],y=r['y'],covered_pixels=int(coverage.sum()),changed_pixels=int(changed.sum()),changed_outside_conservative_geometry=int((changed&~coverage).sum()),draws=draws))
out=dict(result='MEASURED_WORLD_SUBMITTED_GEOMETRY_COVERAGE',frames=len(rows),changed_pixels=sum(r['changed_pixels'] for r in rows),changed_outside_conservative_geometry=sum(r['changed_outside_conservative_geometry'] for r in rows),rows=rows,scope='Actual submitted triangles with viewport/scissor and conservative0.03pixel edge band. Alpha/material discard ignored, so coverage upper bound only; no original world visibility proof or screenpolygon matching.')
(folder/'geometry-coverage-audit.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='rows'})
