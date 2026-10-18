from pathlib import Path
import ctypes as C,json,struct,runpy
p=Path('work/camera');ctx=runpy.run_path(str(p/'test_road_source_ring.py'));events=ctx['events'];joins=ctx['joins'];geo=ctx['geo'];table=ctx['table'];source=C.CDLL(str((p/'road-source-ring-motion-audit.dll').resolve())).nf_road_source_ring;source.argtypes=ctx['fn'].argtypes;clip=C.CDLL(str((p/'road-clip-continuous.dll').resolve())).nf_road_clip_continuous;clip.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_double,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p];span=C.CDLL(str((p/'road-span-transition-at.dll').resolve())).nf_road_span_transition_at;span.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_void_p,C.c_void_p];bounds_by_command={r['command']:r['bounds'] for r in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']};checks=[];changes=[];eps=1e-8
ledger=C.CDLL(str((p/'road-write-ledger.dll').resolve())).nf_road_write_ledger;ledger.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p];motion=[];projection_audit=[]
for event in events:
 join=next(j for j in joins if j['source']==event['source']);g=next(g for g in geo['roads'] if g['surface']==join['surface']);raw=struct.pack('<6I66i',*g['source_attributes_header'],*(v for pair in g['source_attributes'] for v in pair),*([0]*(64-len(g['source_attributes'])*2)));matrix=bytes.fromhex(event['blocks']['2']['hex']);bounds=bounds_by_command[join['command']]
 def ring_at(translation,axis=0):
  points=[point.copy() for point in g['vertices']]
  for point in points:point[axis]+=translation
  out=(C.c_double*320)();n=C.c_uint();assert source((C.c_double*(len(points)*3))(*(v for point in points for v in point)),len(points),raw,matrix,(C.c_int32*3)(120,87,128),table,out,64,C.byref(n))
  projection_audit.append(dict(command=join['command'],axis=axis,translation=translation,fractional_projected_rows=sum(out[i*5+1]!=int(out[i*5+1]) for i in range(n.value))))
  vertices=[[out[i*5],out[i*5+1],out[i*5+1],out[i*5+2],out[i*5+3],out[i*5+4]] for i in range(n.value)];clipped=(C.c_double*768)();cn=C.c_uint();assert clip((C.c_double*(len(vertices)*6))(*(v for row in vertices for v in row)),len(vertices),bounds[0],bounds[1],table,clipped,128,C.byref(cn));return clipped,cn.value
 baseline,bcount=ring_at(0);basewrites=(C.c_int16*(38400*2))();assert ledger(baseline,bcount,(C.c_uint16*4)(*bounds),table,basewrites)
 for axis in range(3):
  for translation in [-64,-8,-1.75,-1.5,-1.25,-.5,-.25,0,.25,.5,1.25,1.5,1.75,8,64]:
   ring,count=ring_at(translation,axis);writes=(C.c_int16*(38400*2))();valid=ledger(ring,count,(C.c_uint16*4)(*bounds),table,writes)
   fractional_rows=sum(ring[i*6+1]!=int(ring[i*6+1]) for i in range(count))
   ring_gap=max(abs(ring[i]-baseline[i]) for i in range(count*6)) if count==bcount else None
   changed=sum(tuple(writes[i*2:i*2+2])!=tuple(basewrites[i*2:i*2+2]) for i in range(38400)) if valid else None
   motion.append(dict(rejected_ring=[list(ring[i*6:i*6+6]) for i in range(count)] if not valid else None,max_projected_xy_change=[max(abs(ring[i*6+k]-baseline[i*6+k]) for i in range(count)) for k in (0,1)] if count==bcount else None,max_ring_component_change=ring_gap,changed_source_winners=changed,command=join['command'],world_axis=axis,world_translation=translation,vertices=count,fractional_vertex_rows=fractional_rows,ledger_accepted=bool(valid),covered_destinations=sum(writes[i*2]>=0 for i in range(38400)) if valid else None))
report=dict(result='DIAGNOSTIC',projected_rows=projection_audit,checks=motion,rejected=sum(not c['ledger_accepted'] for c in motion),scope='Actual world vertices/raw Q14 camera/project/clip path; audits endpoint scheduler acceptance under fractional world movement. No screen polygon matching; no motion smoothness claim.')
(p/'world-road-ledger-axis-motion-audit.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k not in ('checks','projected_rows')});print({axis:dict(total=sum(c['world_axis']==axis for c in motion),rejected=sum(c['world_axis']==axis and not c['ledger_accepted'] for c in motion)) for axis in range(3)})
