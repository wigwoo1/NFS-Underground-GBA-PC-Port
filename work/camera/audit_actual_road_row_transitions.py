from pathlib import Path
import ctypes as C,json,math,collections
p=Path('work/camera');data=json.loads((p/'road-actual-temporal-domain-tests.json').read_text())['checks'];bounds={r['command']:r['bounds'] for r in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']};table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());span=C.CDLL(str((p/'road-span-transition-at.dll').resolve())).nf_road_span_transition_at;span.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_void_p,C.c_void_p];checks=[];summary=collections.Counter()
for interval in data:
 bd=bounds[interval['command']];states=[]
 for phase in interval['phases']:
  ring=phase['ring'];geometry=(C.c_double*(len(ring)*6))(*(v for r in ring for v in r));rows={};top=min(r[1] for r in ring);bottom=max(r[1] for r in ring)
  for row in range(bd[2],bd[3]+1):
   edges=(C.c_double*8)();valid=bool(span(geometry,len(ring),row,table,edges));rows[row]=dict(valid=valid,edges=list(edges) if valid else [],depth_margin=edges[3]-49152 if valid else None)
  scheduled={};row=int(max(bd[2],top));doubled=False
  while row<=bd[3]:
   if rows[row]['valid']:
    if rows[row]['edges'][3]>49152:doubled=True
    scheduled[row]=dict(doubled=doubled,duplicate_rows=[row,row+1] if doubled else [row],span=rows[row])
   row+=2 if doubled else 1
  states.append(dict(phase=phase['phase'],top=top,bottom=bottom,rows=rows,scheduled=scheduled))
 a,b=states[0],states[-1];births=[row for row in a['rows'] if not a['rows'][row]['valid'] and b['rows'][row]['valid']];deaths=[row for row in a['rows'] if a['rows'][row]['valid'] and not b['rows'][row]['valid']];mode=[row for row in a['scheduled'] if row in b['scheduled'] and a['scheduled'][row]['doubled']!=b['scheduled'][row]['doubled']];schedule_births=sorted(set(b['scheduled'])-set(a['scheduled']));schedule_deaths=sorted(set(a['scheduled'])-set(b['scheduled']));summary.update(intervals=1,span_birth_rows=len(births),span_death_rows=len(deaths),doubled_mode_rows=len(mode),scheduled_birth_rows=len(schedule_births),scheduled_death_rows=len(schedule_deaths),top_changed=int(a['top']!=b['top']))
 checks.append(dict(command=interval['command'],begin_a=interval['begin_a'],begin_b=interval['begin_b'],span_birth_rows=births,span_death_rows=deaths,doubled_mode_rows=mode,scheduled_birth_rows=schedule_births,scheduled_death_rows=schedule_deaths,states=states))
report=dict(result='ACTUAL_VISIBILITY_TRANSITIONS_LOCALIZED',summary=dict(summary),checks=checks,scope='Actual sourcepose horizontal-clipped scanrow availability and original sticky doubled schedule at90source phases across18intervals. Explicit rowbirth/death and skip/double transitions, not a continuous coverage policy, bounds/fullscene/timing proof.')
(p/'road-actual-row-transitions.json').write_text(json.dumps(report,indent=2));print(report['summary'])
