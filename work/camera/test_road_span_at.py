from pathlib import Path
import ctypes as C,json,math
p=Path('work/camera');fn=C.CDLL(str((p/'road-span-at.dll').resolve())).nf_road_span_at;fn.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_void_p,C.c_void_p];edge=C.CDLL(str((p/'road-edge-continuous.dll').resolve())).nf_road_edge_continuous;edge.argtypes=[C.c_void_p]*4;table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());checks=empty=0
for road in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']:
 ring=road['clipped_ring'];data=(C.c_double*(len(ring)*6))(*(v for row in ring for v in row));edges=[]
 for i,a in enumerate(ring):
  b=ring[(i+1)%len(ring)]
  if a[1]>b[1]:a,b=b,a
  if a[1]==b[1]:continue
  slopes=(C.c_double*4)();assert edge((C.c_double*6)(*a),(C.c_double*6)(*b),table,slopes);edges.append((a,b,list(slopes)))
 for step in range(641):
  scan=step/4;expected=[]
  for a,b,slope in edges:
   if a[1]<=scan<b[1]:
    dy=scan-a[1];expected.append([a[0]+slope[0]*dy,a[4]+slope[1]*dy,a[5]+slope[2]*dy,a[3]+slope[3]*dy])
  expected.sort(key=lambda v:v[0]);out=(C.c_double*8)(*([77]*8));ok=fn(data,len(ring),scan,table,out)
  if len(expected)>=2 and expected[-1][0]>expected[0][0]:assert ok and list(out)==expected[0]+expected[-1];checks+=1
  else:assert not ok and list(out)==[77]*8;empty+=1
 bad=list(data);bad[-1]=float('nan');out=(C.c_double*8)(*([77]*8));assert not fn((C.c_double*len(bad))(*bad),len(ring),100,table,out);assert list(out)==[77]*8
seams=[]
for road in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']:
 ring=road['clipped_ring'];data=(C.c_double*(len(ring)*6))(*(v for row in ring for v in row))
 for scan in sorted(set(v[1] for v in ring)):
  left=(C.c_double*8)();right=(C.c_double*8)();a=fn(data,len(ring),scan-1e-8,table,left);b=fn(data,len(ring),scan+1e-8,table,right)
  if a and b:seams.append(dict(command=road['command'],row=scan,x_gap=max(abs(left[k]-right[k]) for k in (0,4)),attribute_gap=max(abs(left[k]-right[k]) for k in (1,2,3,5,6,7))))
report=dict(result='PASS',exact_quarter_row_spans=checks,atomic_empty_spans=empty,atomic_invalid_rings=3,topology_seams=seams,scope='World-derived fractional source row edge query; topology seams, paired scheduling, GPU and fullscene motion remain unverified.');(p/'road-span-at-tests.json').write_text(json.dumps(report,indent=2));print(report)
