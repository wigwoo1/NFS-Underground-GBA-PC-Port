from pathlib import Path
import ctypes as C,json
from road_scan_schedule import anchor_schedule,interpolate_schedule,span,apply_vertical_visibility
p=Path('work/camera');table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());data=json.loads((p/'road-actual-row-transitions.json').read_text())['checks'];bounds={r['command']:r['bounds'] for r in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']};checks=[];endpoint_records=0;phase_records=0;supported=0;unsupported=0;invisible_unsupported=0;partial_visible=0
actual={ (v['command'],v['begin_a']):v for v in json.loads((p/'road-actual-temporal-domain-tests.json').read_text())['checks']}
for item in data:
 key=(item['command'],item['begin_a']);poses=actual[key]['phases'];a,b=poses[0]['ring'],poses[-1]['ring'];bd=bounds[item['command']];samples=[]
 for pose,state in zip(poses,item['states']):
  phase=pose['phase'];schedule=interpolate_schedule(a,b,bd,table,state['top'],phase);assert all(0<=r['duplicate']<=1 and 0<=r['lifetime']<=1 for r in schedule)
  if phase in (0.,1.):
   expected=[(float(row),float(v['doubled'])) for row,v in sorted((int(k),v) for k,v in state['scheduled'].items())];assert [(r['source_row'],r['duplicate']) for r in schedule]==expected;endpoint_records+=len(schedule)
  else:phase_records+=len(schedule)
  gated=apply_vertical_visibility(schedule,pose['ring'])
  if phase in (0.,1.):assert all(r['visible_lifetime']==r['lifetime'] for r in gated)
  geometry=(C.c_double*(len(pose['ring'])*6))(*(v for r in pose['ring'] for v in r));support=[]
  for scan in gated:
   edges=(C.c_double*8)();valid=bool(span(geometry,len(pose['ring']),scan['source_row'],table,edges));support.append(valid)
   if phase not in (0.,1.):
    if valid:supported+=1
    else:
     unsupported+=1
     if scan['visible_lifetime']==0:invisible_unsupported+=1
    if 0<scan['vertical_coverage']<1:partial_visible+=1
  samples.append(dict(phase=phase,schedule=schedule,current_span_support=support,gated_schedule=gated))
 # Same actual midpoint top, infinitesimal phase limits test scheduling weights
 # and ordinal row-offset interpolation separately from current geometry.
 top=item['states'][2]['top'];lo=interpolate_schedule(a,b,bd,table,top,.5-1e-8);hi=interpolate_schedule(a,b,bd,table,top,.5+1e-8);assert len(lo)==len(hi);gap=max((abs(x[field]*x['lifetime']-y[field]*y['lifetime']) for x,y in zip(lo,hi) for field in ('source_row','duplicate','lifetime')),default=0);assert gap<1e-4
 checks.append(dict(command=item['command'],begin_a=item['begin_a'],begin_b=item['begin_b'],weighted_midpoint_gap=gap,samples=samples))
vertical_limit_checks=0
for row in (-10.,0.,95.,106.,159.):
 for boundary in (row,row+1.):
  schedule=[dict(ordinal=0,source_row=row,duplicate=0.,lifetime=1.)]
  values=[]
  for epsilon in (-1e-8,1e-8):
   values.append(apply_vertical_visibility(schedule,[[0,row-2],[0,boundary+epsilon]])[0]['visible_lifetime'])
  assert abs(values[0]-values[1])<3e-8
  vertical_limit_checks+=1
assert invisible_unsupported==unsupported
report=dict(result='PASS_SCHEDULE_VERTICAL_COMPONENT',exact_endpoint_scan_records=endpoint_records,vertical_limit_checks=vertical_limit_checks,geometry_invisible_unsupported_spans=invisible_unsupported,partial_vertical_footprints=partial_visible,supported_interior_spans=supported,unsupported_interior_spans=unsupported,interior_scan_records=phase_records,checks=checks,scope='Canonical original source-scan ordinal scheduling for18actualgameintervals with exact endpoint row/duplicate modes and continuous lifetime/offset weights. Ordinal association is a candidate: current fractional-row span support, occlusion/writer ordering/color/GPU/native4K/fullscene/live timing remain unverified; no global motion claim.')
(p/'road-scan-schedule-tests.json').write_text(json.dumps(report,indent=2));print(report['result'],endpoint_records,phase_records)
