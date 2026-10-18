from pathlib import Path
import numpy as np,zlib,json
p=Path('work/camera/prototype-runs');out=[]
for i in range(5):
 a=np.frombuffer(zlib.decompress((p/f'gl-source-world-{i}.rgb.z').read_bytes()),np.uint8).reshape(2160,3840,3);b=np.frombuffer(zlib.decompress((p/f'd3d-matrix_load-world-{i}.rgb.z').read_bytes()),np.uint8).reshape(a.shape)
 y,x=np.where(np.any(a!=b,axis=2)); rows=[]
 for yy,xx in zip(y,x):
  v=a[yy,xx];near=b[max(0,yy-1):yy+2,max(0,xx-1):xx+2];rows.append(dict(x=int(xx),y=int(yy),gl=v.tolist(),d3d=b[yy,xx].tolist(),reference_color_in_neighbor=bool(np.any(np.all(near==v,axis=2)))))
 out.append(dict(frame=i,count=len(rows),reference_color_in_neighbor=sum(r['reference_color_in_neighbor'] for r in rows),pixels=rows))
(p/'d3d-matrix-load-residual-pixels.json').write_text(json.dumps(out,indent=2));print([{k:v for k,v in r.items() if k!='pixels'} for r in out])
