from pathlib import Path
import ctypes as C,json,struct,runpy
p=Path('work/camera');ctx=runpy.run_path(str(p/'test_road_source_ring.py'));events=ctx['events'];joins=ctx['joins'];geo=ctx['geo'];table=ctx['table'];source=C.CDLL(str((p/'road-source-ring-motion-audit.dll').resolve())).nf_road_source_ring;source.argtypes=ctx['fn'].argtypes;clip=C.CDLL(str((p/'road-clip-continuous.dll').resolve())).nf_road_clip_continuous;clip.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_double,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p];span=C.CDLL(str((p/'road-span-transition-at.dll').resolve())).nf_road_span_transition_at;span.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_void_p,C.c_void_p];bounds_by_command={r['command']:r['bounds'] for r in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']};checks=[];changes=[];eps=1e-8
ledger=C.CDLL(str((p/'road-write-ledger.dll').resolve())).nf_road_write_ledger;ledger.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p];motion=[];projection_audit=[]
candidate=C.CDLL(str((p/'road-row-lattice-coverage.dll').resolve())).nf_road_row_lattice_coverage;candidate.argtypes=ledger.argtypes;seams=[];evaluations=0
temporal=C.CDLL(str((p/'road-temporal-padding.dll').resolve())).nf_road_temporal_padding;temporal.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_double,C.c_double,C.c_void_p,C.c_void_p];pad=C.CDLL(str((p/'road-span-padding-segmented.dll').resolve())).nf_road_span_padding_segmented;pad.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_void_p,C.c_void_p];coverage=C.CDLL(str((p/'road-temporal-padding.dll').resolve())).nf_road_interval_coverage;coverage.argtypes=[C.c_double]*3;coverage.restype=C.c_double;verified=[];endpoint_limits=[]
writes=C.CDLL(str((p/'road-temporal-writes.dll').resolve())).nf_road_temporal_writes;writes.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_double,C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p]
def query(a,na,b,nb,current,nc,bounds,phase,d):
 out=(C.c_double*(322*3))();count=C.c_uint();ok=writes(a,na,b,nb,current,nc,(C.c_uint16*4)(*bounds),phase,table,d,out,322,C.byref(count));return ok,[list(out[i*3:i*3+3]) for i in range(count.value)]
endpoint_checks=0;verified=[];endpoint_limits=[];rejected=[]
from road_temporal_sampler import sample_temporal
from road_lattice_sampler import sample_contributors,compose_palette
palettes=(p/'stable-road-display-palettes.bin').read_bytes();roads={r['command']:r for r in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']};audits=json.loads((p/'road-world-motion-color-audit.json').read_text())['checks'];color_checks=[];moving_color_endpoints=0
from road_temporal_filtered_sampler import sample_filtered
failures=json.loads((p/'road-temporal-color-phase-audit.json').read_text())['localized_jumps'];verified=[];endpoint_limits=[]
for event in events:
 join=next(j for j in joins if j['source']==event['source']);g=next(g for g in geo['roads'] if g['surface']==join['surface']);raw=struct.pack('<6I66i',*g['source_attributes_header'],*(v for pair in g['source_attributes'] for v in pair),*([0]*(64-len(g['source_attributes'])*2)));matrix=bytes.fromhex(event['blocks']['2']['hex']);bounds=bounds_by_command[join['command']]
 def ring_at(translation,axis=0):
  points=[point.copy() for point in g['vertices']]
  for point in points:point[axis]+=translation
  out=(C.c_double*320)();n=C.c_uint();assert source((C.c_double*(len(points)*3))(*(v for point in points for v in point)),len(points),raw,matrix,(C.c_int32*3)(120,87,128),table,out,64,C.byref(n))
  projection_audit.append(dict(command=join['command'],axis=axis,translation=translation,fractional_projected_rows=sum(out[i*5+1]!=int(out[i*5+1]) for i in range(n.value))))
  vertices=[[out[i*5],out[i*5+1],out[i*5+1],out[i*5+2],out[i*5+3],out[i*5+4]] for i in range(n.value)];clipped=(C.c_double*768)();cn=C.c_uint();assert clip((C.c_double*(len(vertices)*6))(*(v for row in vertices for v in row)),len(vertices),bounds[0],bounds[1],table,clipped,128,C.byref(cn));return clipped,cn.value
 road=roads[join['command']];texture=(p/f"road-{join['command']}-index-texture.bin").read_bytes()
 for failure in failures:
  if failure['command']!=join['command']:continue
  lo,hi=failure['world_bracket'];axis=failure['axis'];a,na=ring_at(lo,axis);b,nb=ring_at(hi,axis);d=failure['destination'];palette=palettes[d//240*512:(d//240+1)*512];limits=[]
  for phase in failure['phase_bracket']:
   current,nc=ring_at(lo+(hi-lo)*phase,axis);color,contributors=sample_filtered(a,na,b,nb,current,nc,bounds,phase,table,d,texture,road['normalization'],palette);limits.append(dict(color=color,contributors=contributors))
  gap=max(abs(u-v) for u,v in zip(limits[0]['color'][:3],limits[1]['color'][:3]));verified.append(dict(command=join['command'],axis=axis,destination=d,rgb_gap=gap,limits=limits))
 for audit in audits:
  if audit['command']!=join['command']:continue
  lo,hi=audit['world_bracket'];axis=audit['axis'];a,na=ring_at(lo,axis);b,nb=ring_at(hi,axis)
  for change in audit['changed_pixels']:
   d=change['destination'];palette=palettes[d//240*512:(d//240+1)*512]
   for endpoint,near in [(0.,1e-8),(1.,1.-1e-8)]:
    ring,count=(a,na) if endpoint==0 else (b,nb);expected,_=sample_temporal(a,na,b,nb,ring,count,bounds,endpoint,table,d,texture,road['normalization'],palette);actual,_=sample_filtered(a,na,b,nb,ring,count,bounds,endpoint,table,d,texture,road['normalization'],palette);assert expected==actual
    current,nc=ring_at(lo+(hi-lo)*near,axis);limit,_=sample_filtered(a,na,b,nb,current,nc,bounds,near,table,d,texture,road['normalization'],palette);gap=max(abs(u-v) for u,v in zip(expected,limit));endpoint_limits.append(dict(command=join['command'],destination=d,endpoint=endpoint,gap=gap))
 print('filtered localized',join['command'],len(verified),flush=True)
report=dict(result='PASS_LOCALIZED_FILTER_LIMITS' if all(v['rgb_gap']<.001 for v in verified) and all(v['gap']<.001 for v in endpoint_limits) else 'REJECTED_FILTER_LIMITS',checks=verified,endpoint_limits=endpoint_limits,maximum_endpoint_limit_gap=max(v['gap'] for v in endpoint_limits),maximum_rgb_gap=max(v['rgb_gap'] for v in verified),scope='CPU source-row/pair-lane-preserving bilinear palette RGB filtering with source-pose texel-phase residual anchors. Tests26localized prior index thresholds only; endpoints dispatch original sampler, no fullinterval/globalmotion/GPU/gameplay proof.')
(p/'road-temporal-filtered-tests.json').write_text(json.dumps(report,indent=2));print(report['result'],report['maximum_rgb_gap'])
