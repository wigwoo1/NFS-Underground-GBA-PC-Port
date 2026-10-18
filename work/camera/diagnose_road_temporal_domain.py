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
from road_temporal_sampler import sample_temporal
from road_lattice_sampler import sample_contributors,compose_palette
palettes=(p/'stable-road-display-palettes.bin').read_bytes();roads={r['command']:r for r in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']};audits=json.loads((p/'road-world-motion-color-audit.json').read_text())['checks'];color_checks=[];moving_color_endpoints=0
diagnose=C.CDLL(str((p/'road-temporal-writes.dll').resolve())).nf_road_temporal_writes_rejection;diagnose.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_double,C.c_void_p,C.c_uint];diagnose.restype=C.c_uint;checks=[]
unsupported=json.loads((p/'road-temporal-color-phase-audit.json').read_text())['unsupported_queries']
for event in events:
 join=next(j for j in joins if j['source']==event['source']);g=next(g for g in geo['roads'] if g['surface']==join['surface']);raw=struct.pack('<6I66i',*g['source_attributes_header'],*(v for pair in g['source_attributes'] for v in pair),*([0]*(64-len(g['source_attributes'])*2)));matrix=bytes.fromhex(event['blocks']['2']['hex']);bounds=bounds_by_command[join['command']]
 def ring_at(translation,axis=0):
  points=[point.copy() for point in g['vertices']]
  for point in points:point[axis]+=translation
  out=(C.c_double*320)();n=C.c_uint();assert source((C.c_double*(len(points)*3))(*(v for point in points for v in point)),len(points),raw,matrix,(C.c_int32*3)(120,87,128),table,out,64,C.byref(n))
  projection_audit.append(dict(command=join['command'],axis=axis,translation=translation,fractional_projected_rows=sum(out[i*5+1]!=int(out[i*5+1]) for i in range(n.value))))
  vertices=[[out[i*5],out[i*5+1],out[i*5+1],out[i*5+2],out[i*5+3],out[i*5+4]] for i in range(n.value)];clipped=(C.c_double*768)();cn=C.c_uint();assert clip((C.c_double*(len(vertices)*6))(*(v for row in vertices for v in row)),len(vertices),bounds[0],bounds[1],table,clipped,128,C.byref(cn));return clipped,cn.value
 road=roads[join['command']];texture=(p/f"road-{join['command']}-index-texture.bin").read_bytes()
 for rejected in unsupported:
  if rejected['command']!=join['command']:continue
  audit=next(v for v in audits if v['command']==join['command'] and v['axis']==rejected['axis']);lo,hi=audit['world_bracket'];phase=rejected['phase'];a,na=ring_at(lo,rejected['axis']);b,nb=ring_at(hi,rejected['axis']);current,nc=ring_at(lo+(hi-lo)*phase,rejected['axis']);reason=diagnose(a,na,b,nb,current,nc,(C.c_uint16*4)(*bounds),phase,table,rejected['destination']);assert reason;differences=[]
  for row in range(bounds[2],bounds[3]+1):
   values=[]
   for ring,count in [(a,na),(b,nb),(current,nc)]:
    edges=(C.c_double*8)();valid=span(ring,count,row,table,edges);values.append(dict(valid=bool(valid),edges=list(edges)))
   if len({v['valid'] for v in values})>1:differences.append(dict(row=row,states=values))
  checks.append(dict(**rejected,rejection_code=reason,top_rows=[min(r[i*6+1] for i in range(n)) for r,n in [(a,na),(b,nb),(current,nc)]],row_availability_changes=differences,current_ring=[list(current[i*6:i*6+6]) for i in range(nc)]))
report=dict(result='DIAGNOSED',checks=checks,codes=json.loads((p/'road-temporal-writes-rejection-codes.json').read_text()),scope='Exact rejection reasons for25retained unsupported current poses; no domain bypass or visibility fix.')
(p/'road-temporal-domain-diagnosis.json').write_text(json.dumps(report,indent=2));print({code:sum(v['rejection_code']==code for v in checks) for code in set(v['rejection_code'] for v in checks)});print([(c['phase'],[v['row'] for v in c['row_availability_changes']]) for c in checks[:5]])
