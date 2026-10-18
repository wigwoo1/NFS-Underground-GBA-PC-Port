from pathlib import Path
import ctypes as C,json,struct,runpy
p=Path('work/camera');ctx=runpy.run_path(str(p/'test_road_source_ring.py'));events=ctx['events'];joins=ctx['joins'];geo=ctx['geo'];table=ctx['table'];source=C.CDLL(str((p/'road-source-ring-motion-audit.dll').resolve())).nf_road_source_ring;source.argtypes=ctx['fn'].argtypes;clip=C.CDLL(str((p/'road-clip-continuous.dll').resolve())).nf_road_clip_continuous;clip.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_double,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p];span=C.CDLL(str((p/'road-span-transition-at.dll').resolve())).nf_road_span_transition_at;span.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_void_p,C.c_void_p];bounds_by_command={r['command']:r['bounds'] for r in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']};checks=[];changes=[];eps=1e-8
ledger=C.CDLL(str((p/'road-write-ledger.dll').resolve())).nf_road_write_ledger;ledger.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p];motion=[];projection_audit=[]
candidate=C.CDLL(str((p/'road-row-lattice-coverage.dll').resolve())).nf_road_row_lattice_coverage;candidate.argtypes=ledger.argtypes;seams=[];evaluations=0
temporal=C.CDLL(str((p/'road-temporal-padding.dll').resolve())).nf_road_temporal_padding;temporal.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_double,C.c_double,C.c_void_p,C.c_void_p];pad=C.CDLL(str((p/'road-span-padding-segmented.dll').resolve())).nf_road_span_padding_segmented;pad.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_void_p,C.c_void_p];coverage=C.CDLL(str((p/'road-temporal-padding.dll').resolve())).nf_road_interval_coverage;coverage.argtypes=[C.c_double]*3;coverage.restype=C.c_double;verified=[]
for event in events:
 join=next(j for j in joins if j['source']==event['source']);g=next(g for g in geo['roads'] if g['surface']==join['surface']);raw=struct.pack('<6I66i',*g['source_attributes_header'],*(v for pair in g['source_attributes'] for v in pair),*([0]*(64-len(g['source_attributes'])*2)));matrix=bytes.fromhex(event['blocks']['2']['hex']);bounds=bounds_by_command[join['command']]
 def ring_at(translation,axis=0):
  points=[point.copy() for point in g['vertices']]
  for point in points:point[axis]+=translation
  out=(C.c_double*320)();n=C.c_uint();assert source((C.c_double*(len(points)*3))(*(v for point in points for v in point)),len(points),raw,matrix,(C.c_int32*3)(120,87,128),table,out,64,C.byref(n))
  projection_audit.append(dict(command=join['command'],axis=axis,translation=translation,fractional_projected_rows=sum(out[i*5+1]!=int(out[i*5+1]) for i in range(n.value))))
  vertices=[[out[i*5],out[i*5+1],out[i*5+1],out[i*5+2],out[i*5+3],out[i*5+4]] for i in range(n.value)];clipped=(C.c_double*768)();cn=C.c_uint();assert clip((C.c_double*(len(vertices)*6))(*(v for row in vertices for v in row)),len(vertices),bounds[0],bounds[1],table,clipped,128,C.byref(cn));return clipped,cn.value
 for failure in json.loads((p/'world-row-lattice-adaptive-motion.json').read_text())['checks']:
  if failure['command']!=join['command'] or failure['coverage_gap']<=.001:continue
  lo,hi=failure['bracket'];axis=failure['axis'];a,na=ring_at(lo,axis);b,nb=ring_at(hi,axis);row=failure['pixel']//240
  for phase in (0.,1.):
   current,nc=ring_at(lo+(hi-lo)*phase,axis);out=(C.c_double*2)();expected=(C.c_double*2)();endpoint,count=(a,na) if phase==0 else (b,nb);assert pad(endpoint,count,row,table,expected);assert temporal(a,na,b,nb,current,nc,row,phase,table,out);assert list(out)==list(expected)
  values=[]
  for phase in (.5-1e-8,.5+1e-8):
   current,nc=ring_at(lo+(hi-lo)*phase,axis);out=(C.c_double*2)();assert temporal(a,na,b,nb,current,nc,row,phase,table,out);values.append(list(out))
  alpha=[coverage(v[0],v[1],failure['pixel']%240) for v in values];alpha_gap=abs(alpha[0]-alpha[1]);assert alpha_gap<1e-5;gap=max(abs(x-y) for x,y in zip(*values));assert gap<1e-5,gap;verified.append(dict(command=join['command'],axis=axis,row=row,world_bracket=[lo,hi],phase_padding_gap=gap,interval_coverage_gap=alpha_gap,padding_limits=values))
original=0
for road in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']:
 ring=road['clipped_ring'];data=(C.c_double*(len(ring)*6))(*(v for r in ring for v in r))
 for row in range(161):
  expected=(C.c_double*2)();valid=pad(data,len(ring),row,table,expected)
  for phase in (0.,1.):
   out=(C.c_double*2)(77,88);ok=temporal(data,len(ring),data,len(ring),data,len(ring),row,phase,table,out);assert bool(ok)==bool(valid)
   if ok:assert list(out)==list(expected);original+=1
   else:assert list(out)==[77,88]
report=dict(result='PASS',checks=verified,exact_original_endpoint_padding_checks=original,scope='Interior temporal padding residual candidate using actual world-derived current rings across7localized failing world brackets. Exact two pose endpoints and original padding; no final winner coverage, visibility birth/death, UV/color or fullscene/live60fps proof.')
(p/'road-temporal-padding-tests.json').write_text(json.dumps(report,indent=2));print(report)
