from pathlib import Path
import ctypes as C,json,struct,runpy
p=Path('work/camera');ctx=runpy.run_path(str(p/'test_road_source_ring.py'));events=ctx['events'];joins=ctx['joins'];geo=ctx['geo'];table=ctx['table'];source=C.CDLL(str((p/'road-source-ring-motion-audit.dll').resolve())).nf_road_source_ring;source.argtypes=ctx['fn'].argtypes;clip=C.CDLL(str((p/'road-clip-continuous.dll').resolve())).nf_road_clip_continuous;clip.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_double,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p];span=C.CDLL(str((p/'road-span-transition-at.dll').resolve())).nf_road_span_transition_at;span.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_void_p,C.c_void_p];bounds_by_command={r['command']:r['bounds'] for r in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']};checks=[];changes=[];eps=1e-8
ledger=C.CDLL(str((p/'road-write-ledger.dll').resolve())).nf_road_write_ledger;ledger.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p];motion=[];projection_audit=[]
candidate=C.CDLL(str((p/'road-row-lattice-coverage.dll').resolve())).nf_road_row_lattice_coverage;candidate.argtypes=ledger.argtypes;seams=[];evaluations=0
temporal=C.CDLL(str((p/'road-temporal-padding.dll').resolve())).nf_road_temporal_padding;temporal.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_double,C.c_double,C.c_void_p,C.c_void_p];pad=C.CDLL(str((p/'road-span-padding-segmented.dll').resolve())).nf_road_span_padding_segmented;pad.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_void_p,C.c_void_p];coverage=C.CDLL(str((p/'road-temporal-padding.dll').resolve())).nf_road_interval_coverage;coverage.argtypes=[C.c_double]*3;coverage.restype=C.c_double;verified=[]
writes=C.CDLL(str((p/'road-temporal-writes.dll').resolve())).nf_road_temporal_writes;writes.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_double,C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p]
def query(a,na,b,nb,current,nc,bounds,phase,d):
 out=(C.c_double*(322*3))();count=C.c_uint();ok=writes(a,na,b,nb,current,nc,(C.c_uint16*4)(*bounds),phase,table,d,out,322,C.byref(count));return ok,[list(out[i*3:i*3+3]) for i in range(count.value)]
endpoint_checks=0;verified=[];rejected=[]
for event in events:
 join=next(j for j in joins if j['source']==event['source']);g=next(g for g in geo['roads'] if g['surface']==join['surface']);raw=struct.pack('<6I66i',*g['source_attributes_header'],*(v for pair in g['source_attributes'] for v in pair),*([0]*(64-len(g['source_attributes'])*2)));matrix=bytes.fromhex(event['blocks']['2']['hex']);bounds=bounds_by_command[join['command']]
 def ring_at(translation,axis=0):
  points=[point.copy() for point in g['vertices']]
  for point in points:point[axis]+=translation
  out=(C.c_double*320)();n=C.c_uint();assert source((C.c_double*(len(points)*3))(*(v for point in points for v in point)),len(points),raw,matrix,(C.c_int32*3)(120,87,128),table,out,64,C.byref(n))
  projection_audit.append(dict(command=join['command'],axis=axis,translation=translation,fractional_projected_rows=sum(out[i*5+1]!=int(out[i*5+1]) for i in range(n.value))))
  vertices=[[out[i*5],out[i*5+1],out[i*5+1],out[i*5+2],out[i*5+3],out[i*5+4]] for i in range(n.value)];clipped=(C.c_double*768)();cn=C.c_uint();assert clip((C.c_double*(len(vertices)*6))(*(v for row in vertices for v in row)),len(vertices),bounds[0],bounds[1],table,clipped,128,C.byref(cn));return clipped,cn.value
 for failure in json.loads((p/'world-row-lattice-adaptive-motion.json').read_text())['checks']:
  if failure['command']!=join['command'] or not failure['source_rings']:continue
  lo,hi=failure['bracket'];axis=failure['axis'];a,na=ring_at(lo,axis);b,nb=ring_at(hi,axis);d=failure['pixel'];values=[]
  for phase in (0.,1.):
   current,nc=(a,na) if phase==0 else (b,nb);ok,result=query(a,na,b,nb,current,nc,bounds,phase,d);assert ok
   original=(C.c_int16*(38400*2))();assert ledger(current,nc,(C.c_uint16*4)(*bounds),table,original);row,x=original[d*2:d*2+2];expected=[] if row<0 else [[row,x,1.]];assert result==expected,(d,phase,result,expected);endpoint_checks+=1
  for phase in (.5-1e-8,.5+1e-8):
   current,nc=ring_at(lo+(hi-lo)*phase,axis);ok,result=query(a,na,b,nb,current,nc,bounds,phase,d);
   if not ok:
    rejected.append(dict(command=join["command"],axis=axis,pixel=d,phase=phase,counts=[na,nb,nc],fractional_current_rows=sum(current[i*6+1]!=int(current[i*6+1]) for i in range(nc))));break
   values.append(result)
  if len(values)!=2:continue
  phase_coverage=[]
  for phase in (0.,.25,.5,.75,1.):
   current,nc=ring_at(lo+(hi-lo)*phase,axis);ok,result=query(a,na,b,nb,current,nc,bounds,phase,d);assert ok;coverage_sum=sum(v[2] for v in result);assert 0<=coverage_sum<=1+1e-12;phase_coverage.append(coverage_sum)
  alphas=[sum(v[2] for v in result) for result in values];gap=abs(alphas[0]-alphas[1]);assert gap<1e-5,(failure,gap);verified.append(dict(command=join['command'],axis=axis,pixel=d,coverage_gap=gap,contributors=values,phase_coverage=phase_coverage));print(verified[-1],flush=True)
phase_samples=[]
original_checks=0
for road in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']:
 ring=road['clipped_ring'];data=(C.c_double*(len(ring)*6))(*(v for r in ring for v in r));original=(C.c_int16*(38400*2))();assert ledger(data,len(ring),(C.c_uint16*4)(*road['bounds']),table,original)
 for d in range(38400):
  ok,result=query(data,len(ring),data,len(ring),data,len(ring),road['bounds'],0.,d);assert ok;row,x=original[d*2:d*2+2];expected=[] if row<0 else [[row,x,1.]];assert result==expected,(road['command'],d,result,expected);original_checks+=1
 print('original endpoint',road['command'],original_checks,flush=True)
assert len(verified)==7 and not rejected,(verified,rejected)
report=dict(result='PASS',rejected_boundaries=rejected,localized_world_boundaries=verified,original_endpoint_winners=original_checks,moving_anchor_endpoint_checks=endpoint_checks,scope='Diagnostic integer anchor sourceY with fractional current sourceY and common source-row/doubled schedule temporal interval contributors, exact original winners at phase0 plus seven two-anchor endpoints. Coverage continuity only; texture lane/pair color transitions, changing topology/schedules/fractional anchor sourceY, native4K fullscene/live timing unverified.')
(p/'road-temporal-writes-tests.json').write_text(json.dumps(report,indent=2));print(report['result'])
