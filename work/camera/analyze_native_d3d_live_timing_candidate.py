"""Native callback submission timing; explicitly excludes successful visible scanout."""
import json,sys,math,statistics,collections
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());sources={(s['epoch'],s['publication']):s for s in r['sky_capture_records']}
rows=r['presentation_samples'];phase_checks=0;moving=0;previous=None;late=[];draw=[];present=[]
for row in rows:
 a=sources[row['epoch'],row['source_older']];b=sources[row['epoch'],row['refresh']]
 delta=((b['angle']-a['angle']+8192)&16383)-8192;phase=(((a['angle']&16383)+delta*row['alpha'])*240/4096)%240
 assert row['sky_phase_mode']=='continuous_angle' and math.isclose(row['sky_fraction'],phase-math.floor(phase),abs_tol=1e-10)
 phase_checks+=1
 if previous and (row['epoch'],row['source_older'],row['refresh'])==previous[:3] and delta and row['alpha']!=previous[3]:
  assert not math.isclose(phase,previous[4],abs_tol=1e-10);moving+=1
 previous=(row['epoch'],row['source_older'],row['refresh'],row['alpha'],phase)
 t=row['callback_timing']
 if 'draw_end_ns' in t:draw.append((t['draw_end_ns']-t['draw_begin_ns'])/1e6)
 if 'present_end_ns' in t:
  present.append((t['present_end_ns']-t['present_begin_ns'])/1e6);late.append((t['present_begin_ns']-row['presentation_deadline_ns'])/1e6)
 if row['native_result']!=1:assert row['native_committed_sample'] is None

def stats(v):
 v=sorted(v);return dict(count=len(v),median_ms=statistics.median(v),p95_ms=v[min(len(v)-1,int(len(v)*.95))],max_ms=max(v)) if v else None
assert len(r['pause_events'])==3
out=dict(result='PASS_NATIVE_LIVE_TELEMETRY',original_updates=r['original_updates'],samples=len(rows),sky_phase_checks=phase_checks,moving_same_pair_transitions=moving,pause_events=len(r['pause_events']),draw_callback=stats(draw),present_callback=stats(present),deadline_lateness=stats(late),native_results=dict(collections.Counter(x['native_result'] for x in rows)),successful_presentations=sum(x['native_result']==1 for x in rows),smooth_60fps_verified=False,physical_controller_verified=False,scope='Recorded scripted steering/repeated pause live original-clock native path; callback times include worker scheduling. Native status outcomes retained; successful Present calls do not certify scanout or rendered pixel motion.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))

