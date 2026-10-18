from pathlib import Path
import ctypes as C,json
p=Path('work/camera');edge=C.CDLL(str((p/'road-edge-continuous.dll').resolve())).nf_road_edge_continuous;edge.argtypes=[C.c_void_p]*4;table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());roads=[]
for road in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']:
 records=[]
 for i,a in enumerate(road['clipped_ring']):
  b=road['clipped_ring'][(i+1)%len(road['clipped_ring'])];source=(i,(i+1)%len(road['clipped_ring']))
  if a[1]>b[1]:a,b=b,a
  if a[1]==b[1]:records.append(dict(edge=source,horizontal=True,row=a[1],x_extent=abs(a[0]-b[0])));continue
  out=(C.c_double*4)();assert edge((C.c_double*6)(*a),(C.c_double*6)(*b),table,out);fields=[0,4,5,3];residual=[a[k]+out[j]*(b[1]-a[1])-b[k] for j,k in enumerate(fields)];records.append(dict(edge=source,horizontal=False,begin=a[1],end=b[1],height=b[1]-a[1],slope=list(out),endpoint_residual_x_u_v_q=residual))
 roads.append(dict(command=road['command'],edges=records))
report=dict(result='MEASURED',roads=roads,scope='Source edge endpoint residual audit; horizontal edges may legitimately change scanline intersection extent. No automatic seam smoothing.');(p/'road-span-topology-diagnosis.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
