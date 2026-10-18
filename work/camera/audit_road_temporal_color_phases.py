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
sweep_checks=[];localized=[];evaluations=0;unsupported=[]
for event in events:
 join=next(j for j in joins if j['source']==event['source']);g=next(g for g in geo['roads'] if g['surface']==join['surface']);raw=struct.pack('<6I66i',*g['source_attributes_header'],*(v for pair in g['source_attributes'] for v in pair),*([0]*(64-len(g['source_attributes'])*2)));matrix=bytes.fromhex(event['blocks']['2']['hex']);bounds=bounds_by_command[join['command']]
 def ring_at(translation,axis=0):
  points=[point.copy() for point in g['vertices']]
  for point in points:point[axis]+=translation
  out=(C.c_double*320)();n=C.c_uint();assert source((C.c_double*(len(points)*3))(*(v for point in points for v in point)),len(points),raw,matrix,(C.c_int32*3)(120,87,128),table,out,64,C.byref(n))
  projection_audit.append(dict(command=join['command'],axis=axis,translation=translation,fractional_projected_rows=sum(out[i*5+1]!=int(out[i*5+1]) for i in range(n.value))))
  vertices=[[out[i*5],out[i*5+1],out[i*5+1],out[i*5+2],out[i*5+3],out[i*5+4]] for i in range(n.value)];clipped=(C.c_double*768)();cn=C.c_uint();assert clip((C.c_double*(len(vertices)*6))(*(v for row in vertices for v in row)),len(vertices),bounds[0],bounds[1],table,clipped,128,C.byref(cn));return clipped,cn.value
 road=roads[join['command']];texture=(p/f"road-{join['command']}-index-texture.bin").read_bytes()
 for audit in audits:
  if audit['command']!=join['command']:continue
  lo,hi=audit['world_bracket'];axis=audit['axis'];a,na=ring_at(lo,axis);b,nb=ring_at(hi,axis);rings={}
  def evaluate(phase,destination):
   global evaluations
   if phase not in rings:rings[phase]=ring_at(lo+(hi-lo)*phase,axis)
   current,nc=rings[phase];palette=palettes[destination//240*512:(destination//240+1)*512];
   try:color,contributors=sample_temporal(a,na,b,nb,current,nc,bounds,phase,table,destination,texture,road['normalization'],palette)
   except AssertionError as error:
    unsupported.append(dict(command=join['command'],axis=axis,destination=destination,phase=phase,reason=str(error)));return None
   evaluations+=1
   return dict(color=color,contributors=contributors)
  for change in audit['changed_pixels']:
   d=change['destination'];values=[evaluate(i/32,d) for i in range(33)];transitions=0
   if any(v is None for v in values):continue
   signature=lambda v:tuple((c['source_row'],c['source_x'],c['index']) for c in v['contributors'] if c['weight']>1e-8)
   for i in range(32):
    left,right=values[i],values[i+1]
    if left['color'][3]<.1 or right['color'][3]<.1 or signature(left)==signature(right):continue
    lower,upper=i/32,(i+1)/32;leftsig=signature(left)
    for _ in range(24):
     mid=(lower+upper)/2;v=evaluate(mid,d)
     if v is None:break
     if signature(v)==leftsig:lower=mid;left=v
     else:upper=mid;right=v
    gap=max(abs(u-v) for u,v in zip(left['color'][:3],right['color'][:3]));alpha_gap=abs(left['color'][3]-right['color'][3])
    if gap>.001 or alpha_gap>.001:
     localized.append(dict(command=join['command'],axis=axis,destination=d,world_bracket=[lo,hi],phase_bracket=[lower,upper],rgb_gap=gap,alpha_gap=alpha_gap,before=left,after=right));transitions+=1
   sweep_checks.append(dict(command=join['command'],axis=axis,destination=d,samples=33,localized_jumps=transitions,maximum_sample_rgb_step=max(max(abs(u-v) for u,v in zip(values[i]['color'][:3],values[i+1]['color'][:3])) for i in range(32))))
  print('sweep',join['command'],axis,'checks',len(sweep_checks),'jumps',len(localized),flush=True)
report=dict(result='REJECTED_INDEXED_COLOR_CONTINUITY' if localized else ('REJECTED_UNSUPPORTED_INTERVALS' if unsupported else 'NO_JUMPS_FOUND_IN_SAMPLED_INTERVALS'),evaluations=evaluations,unsupported_queries=unsupported,checks=sweep_checks,localized_jumps=localized,scope='33phase full tinyworld diagnostic interval samples with24-step adaptive indexed contributor transition localization. Nearest texture/palette discontinuities assessed separately from coverage. No actualgameframe interval or global continuity proof.')
(p/'road-temporal-color-phase-audit.json').write_text(json.dumps(report,indent=2));print(report['result'],evaluations,len(localized))
