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
  lo,hi=audit['world_bracket'];axis=audit['axis'];a,na=ring_at(lo,axis);b,nb=ring_at(hi,axis)
  for change in audit['changed_pixels']:
   destination=change['destination'];palette=palettes[destination//240*512:(destination//240+1)*512];limits=[]
   for phase in (0.,1.):
    current,nc=(a,na) if phase==0 else (b,nb);ring=[list(current[i*6:i*6+6]) for i in range(nc)];expected=compose_palette(sample_contributors(ring,bounds,texture,road['normalization'],table,destination),palette);actual,_=sample_temporal(a,na,b,nb,current,nc,bounds,phase,table,destination,texture,road['normalization'],palette);assert actual==expected,(join['command'],destination,phase,actual,expected);moving_color_endpoints+=1
   for phase in (.5-1e-8,.5+1e-8):
    current,nc=ring_at(lo+(hi-lo)*phase,axis);color,contributors=sample_temporal(a,na,b,nb,current,nc,bounds,phase,table,destination,texture,road['normalization'],palette);limits.append(dict(color=color,contributors=contributors))
   gap=max(abs(u-v) for u,v in zip(limits[0]['color'][:3],limits[1]['color'][:3]));alpha_gap=abs(limits[0]['color'][3]-limits[1]['color'][3]);color_checks.append(dict(command=join['command'],axis=axis,destination=destination,original_transition_class=change['transition_class'],rgb_gap=gap,alpha_gap=alpha_gap,limits=limits))
 print('motion color checked',join['command'],len(color_checks),flush=True)
original_checks=0
for cmd,road in roads.items():
 ring=road['clipped_ring'];data=(C.c_double*(len(ring)*6))(*(v for row in ring for v in row));payload=(p/f'stable-road-{cmd}-all-original-samples.bin').read_bytes();immutable={struct.unpack_from('<IB',payload,i)[0]:struct.unpack_from('<IB',payload,i)[1] for i in range(0,len(payload),5)};texture=(p/f'road-{cmd}-index-texture.bin').read_bytes()
 for d,index in immutable.items():
  palette=palettes[d//240*512:(d//240+1)*512];color,contributors=sample_temporal(data,len(ring),data,len(ring),data,len(ring),road['bounds'],0.,table,d,texture,road['normalization'],palette);assert len(contributors)==1 and contributors[0]['index']==index and color[3]==1.,(cmd,d,index,contributors);original_checks+=1
 print('original texture checked',cmd,original_checks,flush=True)
failures=[c for c in color_checks if c['rgb_gap']>.001 or c['alpha_gap']>.001]
report=dict(result='PASS_LOCAL_LIMITS' if not failures else 'REJECTED_COLOR_CONTINUITY',exact_original_index_checks=original_checks,moving_color_endpoint_checks=moving_color_endpoints,motion_checks=color_checks,discontinuous_checks=len(failures),maximum_rgb_gap=max(c['rgb_gap'] for c in color_checks),maximum_alpha_gap=max(c['alpha_gap'] for c in color_checks),scope='CPU temporal contributor coverage + current geometry continuous paired UV + repeated nearest indexed/palette sampling at seven tinyworld bracket midphase limits. Original15400 indices checked. No actualgameframe interval/GPU/fullscene/native4K/live timing proof.')
(p/'road-temporal-sampler-tests.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k!='motion_checks'})
