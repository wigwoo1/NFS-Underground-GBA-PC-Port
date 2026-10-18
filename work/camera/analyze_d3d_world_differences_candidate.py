import json,zlib
from pathlib import Path
import numpy as np
p=Path('work/camera/prototype-runs'); rows=[]
for i in range(5):
 a=np.frombuffer(zlib.decompress((p/f'gl-source-world-{i}.rgb.z').read_bytes()),np.uint8).reshape(2160,3840,3)
 b=np.frombuffer(zlib.decompress((p/f'd3d-source-world-{i}.rgb.z').read_bytes()),np.uint8).reshape(a.shape)
 mask=np.any(a!=b,axis=2); y,x=np.where(mask); delta=np.abs(a.astype(np.int16)-b.astype(np.int16))
 edge=np.zeros(mask.shape,bool)
 edge[1:] |= np.any(a[1:]!=a[:-1],axis=2);edge[:-1] |= np.any(a[1:]!=a[:-1],axis=2)
 edge[:,1:] |= np.any(a[:,1:]!=a[:,:-1],axis=2);edge[:,:-1] |= np.any(a[:,1:]!=a[:,:-1],axis=2)
 rows.append(dict(frame=i,different_pixels=int(mask.sum()),bounding_box=[int(x.min()),int(y.min()),int(x.max()),int(y.max())],near_reference_color_edge=int((mask&edge).sum()),away_from_reference_color_edge=int((mask&~edge).sum()),channel_delta_histogram={str(k):int((delta[mask]==k).sum()) for k in [0,1,2,8,16,255]},row_bands=[int(mask[j:j+216].sum()) for j in range(0,2160,216)]))
r=dict(scope='Five offscreen world/sky images, HUD excluded. Edge adjacency is descriptive and does not excuse mismatches.',frames=rows)
(p/'d3d-world-difference-localization.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
