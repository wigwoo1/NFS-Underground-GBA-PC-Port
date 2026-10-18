from pathlib import Path
import ctypes as C,json,struct,runpy
p=Path('work/camera');ctx=runpy.run_path(str(p/'test_road_source_ring.py'));events=ctx['events'];joins=ctx['joins'];geo=ctx['geo'];table=ctx['table'];source=ctx['fn'];clip=C.CDLL(str((p/'road-clip-continuous.dll').resolve())).nf_road_clip_continuous;clip.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_double,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p];span=C.CDLL(str((p/'road-span-transition-at.dll').resolve())).nf_road_span_transition_at;span.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_void_p,C.c_void_p];bounds_by_command={r['command']:r['bounds'] for r in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']};checks=[];changes=[];eps=1e-8
for event in events:
 join=next(j for j in joins if j['source']==event['source']);g=next(g for g in geo['roads'] if g['surface']==join['surface']);raw=struct.pack('<6I66i',*g['source_attributes_header'],*(v for pair in g['source_attributes'] for v in pair),*([0]*(64-len(g['source_attributes'])*2)));matrix=bytes.fromhex(event['blocks']['2']['hex']);bounds=bounds_by_command[join['command']]
 def ring_at(translation):
  points=[point.copy() for point in g['vertices']]
  for point in points:point[0]+=translation
  out=(C.c_double*320)();n=C.c_uint();assert source((C.c_double*(len(points)*3))(*(v for point in points for v in point)),len(points),raw,matrix,(C.c_int32*3)(120,87,128),table,out,64,C.byref(n))
  vertices=[[out[i*5],out[i*5+1],out[i*5+1],out[i*5+2],out[i*5+3],out[i*5+4]] for i in range(n.value)];clipped=(C.c_double*768)();cn=C.c_uint();assert clip((C.c_double*(len(vertices)*6))(*(v for row in vertices for v in row)),len(vertices),bounds[0],bounds[1],table,clipped,128,C.byref(cn));return clipped,cn.value
 for translation in [-.5,-.25,0,.25,.5]:
  left,ln=ring_at(translation-eps);right,rn=ring_at(translation+eps)
  for row in [90.25,94.5,95.75,99.5,106.5,120.25]:
   a=(C.c_double*8)();b=(C.c_double*8)();ao=span(left,ln,row,table,a);bo=span(right,rn,row,table,b)
   if ao!=bo:changes.append(dict(command=join['command'],translation=translation,row=row));continue
   if not ao:continue
   gap=max(abs(x-y) for x,y in zip(a,b));assert gap<.1,(join['command'],translation,row,gap);checks.append(dict(command=join['command'],translation=translation,row=row,gap=gap))
assert checks and not changes,changes
report=dict(result='PASS',world_translation_two_sided_spans=len(checks),epsilon=eps,max_span_component_gap=max(c['gap'] for c in checks),coverage_changes=changes,scope='Fixed raw Q14 camera, world X movement through near/projection/horizontal clipping/span correction; sampled positions only, not rotating camera/GPU/fullscene motion.',checks=checks);(p/'world-road-span-motion-tests.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k!='checks'})
