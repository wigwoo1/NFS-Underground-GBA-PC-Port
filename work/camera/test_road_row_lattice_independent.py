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
for f in json.loads((p/'world-road-ledger-axis-motion-audit.json').read_text())['checks']:
 if f['ledger_accepted']:continue
 ring=f['rejected_ring'];active=[i for i,r in enumerate(ring) if r[1]!=math.floor(r[1])];expected=[[0.,0.,0.] for i in range(38400)]
 for bits in itertools.product((0,1),repeat=len(active)):
  corner=[r.copy() for r in ring];weight=1.
  for i,bit in zip(active,bits):
   fraction=ring[i][1]-math.floor(ring[i][1]);weight*=fraction if bit else 1-fraction;corner[i][1]=math.floor(ring[i][1])+bit
  for destination,(row,x) in python_ledger(corner,bounds[f['command']]).items():
   expected[destination][0]+=weight*row;expected[destination][1]+=weight*x;expected[destination][2]+=weight
 out=(C.c_double*(38400*3))();data=(C.c_double*(len(ring)*6))(*(v for r in ring for v in r));assert candidate(data,len(ring),(C.c_uint16*4)(*bounds[f['command']]),table,out)
 maxgap=max(abs(out[i*3+k]-expected[i][k]) for i in range(38400) for k in range(3));assert maxgap<1e-10,maxgap
 checks.append(dict(command=f['command'],axis=f['world_axis'],translation=f['world_translation'],destinations=38400,corner_ledgers=2**len(active),maximum_gap=maxgap))
report=dict(result='PASS',checks=checks,scope='Independent Python write-order scheduler and fractional corner summation versus C candidate. Shared verified C edge slope primitive; not independent geometric silhouette or color oracle.');(p/'road-row-lattice-independent-tests.json').write_text(json.dumps(report,indent=2));print(report)
