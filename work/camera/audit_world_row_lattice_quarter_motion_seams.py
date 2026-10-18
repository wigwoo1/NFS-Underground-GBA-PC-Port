from pathlib import Path
import ctypes as C,json,struct,runpy
p=Path('work/camera');ctx=runpy.run_path(str(p/'test_road_source_ring.py'));events=ctx['events'];joins=ctx['joins'];geo=ctx['geo'];table=ctx['table'];source=C.CDLL(str((p/'road-source-ring-motion-audit.dll').resolve())).nf_road_source_ring;source.argtypes=ctx['fn'].argtypes;clip=C.CDLL(str((p/'road-clip-continuous.dll').resolve())).nf_road_clip_continuous;clip.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_double,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p];span=C.CDLL(str((p/'road-span-transition-at.dll').resolve())).nf_road_span_transition_at;span.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_void_p,C.c_void_p];bounds_by_command={r['command']:r['bounds'] for r in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']};checks=[];changes=[];eps=1e-8
ledger=C.CDLL(str((p/'road-write-ledger.dll').resolve())).nf_road_write_ledger;ledger.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p];motion=[];projection_audit=[]
candidate=C.CDLL(str((p/'road-row-lattice-coverage.dll').resolve())).nf_road_row_lattice_coverage;candidate.argtypes=ledger.argtypes;seams=[]
for event in events:
 join=next(j for j in joins if j['source']==event['source']);g=next(g for g in geo['roads'] if g['surface']==join['surface']);raw=struct.pack('<6I66i',*g['source_attributes_header'],*(v for pair in g['source_attributes'] for v in pair),*([0]*(64-len(g['source_attributes'])*2)));matrix=bytes.fromhex(event['blocks']['2']['hex']);bounds=bounds_by_command[join['command']]
 def ring_at(translation,axis=0):
  points=[point.copy() for point in g['vertices']]
  for point in points:point[axis]+=translation
  out=(C.c_double*320)();n=C.c_uint();assert source((C.c_double*(len(points)*3))(*(v for point in points for v in point)),len(points),raw,matrix,(C.c_int32*3)(120,87,128),table,out,64,C.byref(n))
  projection_audit.append(dict(command=join['command'],axis=axis,translation=translation,fractional_projected_rows=sum(out[i*5+1]!=int(out[i*5+1]) for i in range(n.value))))
  vertices=[[out[i*5],out[i*5+1],out[i*5+1],out[i*5+2],out[i*5+3],out[i*5+4]] for i in range(n.value)];clipped=(C.c_double*768)();cn=C.c_uint();assert clip((C.c_double*(len(vertices)*6))(*(v for row in vertices for v in row)),len(vertices),bounds[0],bounds[1],table,clipped,128,C.byref(cn));return clipped,cn.value
 for axis in range(3):
  for translation in [i/4 for i in range(-32,33)]:
   results=[];rings=[]
   for side in (-1,1):
    ring,count=ring_at(translation+side*1e-8,axis);out=(C.c_double*(38400*3))();assert candidate(ring,count,(C.c_uint16*4)(*bounds),table,out),(join['command'],axis,translation,side);results.append(out);rings.append([list(ring[i*6:i*6+6]) for i in range(count)])
   a,b=results;coveragegap=max(abs(a[i*3+2]-b[i*3+2]) for i in range(38400));momentgap=max(abs(x-y) for x,y in zip(a,b));jumps=[i for i in range(38400) if abs(a[i*3+2]-b[i*3+2])>.001]
   seams.append(dict(command=join['command'],axis=axis,translation=translation,coverage_gap=coveragegap,moment_gap=momentgap,jumping_destinations=jumps,source_rings=rings if jumps else None))
report=dict(result='REJECTED_FOR_WORLD_MOTION' if any(c['jumping_destinations'] for c in seams) else 'SAMPLED_LIMITS_PASS',checks=seams,scope='Actual world-axis translations through fixed raw Q14 camera/near/project/clip; row-lattice coverage moments across quarter-unit world anchors. Sampled translations only; no rotating camera/fullscene/GPU/color proof.')
(p/'world-row-lattice-quarter-motion-seams.json').write_text(json.dumps(report,indent=2));print(dict(result=report['result'],seams=len(seams),jumping_seams=sum(bool(c['jumping_destinations']) for c in seams),maximum_coverage_gap=max(c['coverage_gap'] for c in seams),maximum_moment_gap=max(c['moment_gap'] for c in seams)))
