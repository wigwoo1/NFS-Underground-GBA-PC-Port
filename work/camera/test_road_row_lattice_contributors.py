from pathlib import Path
import ctypes as C,json,math,itertools
p=Path('work/camera');table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());edge=C.CDLL(str((p/'road-edge-continuous.dll').resolve())).nf_road_edge_continuous;edge.argtypes=[C.c_void_p]*4;candidate=C.CDLL(str((p/'road-row-lattice-coverage.dll').resolve())).nf_road_row_lattice_coverage;candidate.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p];bounds={r['command']:r['bounds'] for r in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']};checks=[]
def python_ledger(ring,bound):
 edges=[]
 for i,a in enumerate(ring):
  b=ring[(i+1)%len(ring)]
  if a[1]>b[1]:a,b=b,a
  if a[1]==b[1]:continue
  slopes=(C.c_double*4)();assert edge((C.c_double*6)(*a),(C.c_double*6)(*b),table,slopes);edges.append((a,b,list(slopes)))
 scan=max(bound[2],min(r[1] for r in ring));doubled=False;writes={}
 while scan<=bound[3]:
  active=sorted((a[0]+s[0]*(scan-a[1]),a[3]+s[3]*(scan-a[1])) for a,b,s in edges if a[1]<=scan<b[1])
  if len(active)>=2 and active[-1][0]>active[0][0]:
   doubled=doubled or active[0][1]>49152;start=2*math.floor(active[0][0]/2);width=math.floor((active[-1][0]-active[0][0])/2)+2
   for pair in range(width):
    for duplicate in range(2 if doubled else 1):
     for lane in range(2):
      x=start+pair*2+lane;destination=(int(scan)+duplicate)*240+x
      if 0<=destination<38400:writes[destination]=(scan,x)
  scan+=2 if doubled else 1
 return writes

contributors=C.CDLL(str((p/'road-row-lattice-coverage.dll').resolve())).nf_road_row_lattice_contributors;contributors.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p];checks=[];atomic=0
for fixture in json.loads((p/'world-road-ledger-axis-motion-audit.json').read_text())['checks']:
 if fixture['ledger_accepted']:continue
 ring=fixture['rejected_ring'];active=[i for i,r in enumerate(ring) if r[1]!=math.floor(r[1])];data=(C.c_double*(len(ring)*6))(*(v for r in ring for v in r));bound=(C.c_uint16*4)(*bounds[fixture['command']]);moments=(C.c_double*(38400*3))();assert candidate(data,len(ring),bound,table,moments)
 partial=[i for i in range(38400) if 1e-12<moments[i*3+2]<1-1e-12];covered=[i for i in range(38400) if moments[i*3+2]>0];targets=sorted(set(partial[:8]+covered[::max(1,len(covered)//8)]+[0,38399]));oracle={i:[] for i in targets}
 for mask in range(1<<len(active)):
  corner=[r.copy() for r in ring];weight=1.
  for k,i in enumerate(active):
   bit=(mask>>k)&1;fraction=ring[i][1]-math.floor(ring[i][1]);weight*=fraction if bit else 1-fraction;corner[i][1]=math.floor(ring[i][1])+bit
  writes=python_ledger(corner,bounds[fixture['command']])
  for i in targets:
   if i in writes:oracle[i].append([float(mask),float(writes[i][0]),float(writes[i][1]),weight])
 for destination in targets:
  out=(C.c_double*(4096*4))();count=C.c_uint(77);assert contributors(data,len(ring),bound,table,destination,out,4096,C.byref(count));actual=[list(out[i*4:i*4+4]) for i in range(count.value)];assert actual==oracle[destination]
  reconstruction=[sum(v[1]*v[3] for v in actual),sum(v[2]*v[3] for v in actual),sum(v[3] for v in actual)];assert all(abs(x-y)<1e-10 for x,y in zip(reconstruction,moments[destination*3:destination*3+3]))
 sentinel=(C.c_double*4)(77,77,77,77);count=C.c_uint(77);assert not contributors(data,len(ring),bound,table,covered[0],sentinel,0,C.byref(count));assert list(sentinel)==[77]*4 and count.value==77;atomic+=1
 checks.append(dict(command=fixture['command'],axis=fixture['world_axis'],translation=fixture['world_translation'],exact_contributor_queries=len(targets)))
report=dict(result='PASS',checks=checks,atomic_capacity_failures=atomic,scope='C per-corner mask/source row/X/weight exactly matches independent Python write-order oracle at selected covered/partial/empty destinations; moments reconstructed. Shared C edge primitive; texture/color sampling still pending.')
(p/'road-row-lattice-contributor-tests.json').write_text(json.dumps(report,indent=2));print(report)
