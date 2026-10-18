"""Join bounded producer capacity waits to actual consumer capacity releases."""
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());s=r['submit_retention']['whole_submission_space_wait'];d=r['boundary_retention']['complete_dequeues'];g=r['bounded_diagnostic_stats']['whole_run_api_intervals']['long_intervals']
assert s['dropped']==0 and s['long_total']==len(s['records'])
assert d['dropped']==0 and d['total']==len(d['records'])
assert g['dropped']==0 and g['total']==len(g['records'])
rows=[]
for submit in s['records']:
 if submit['replay']:continue
 a=submit['submit_begin_ns'];b=a+submit['space_wait_ns'];end=submit['submit_end_ns']
 # popped_ns is sampled immediately after capacity release; producer may wake first.
 releases=[x for x in d['records'] if a<=x['popped_ns']<=end]
 row=dict(scene_identity=submit['scene_identity'],wait_ms=(b-a)/1e6,release_candidates=len(releases))
 if releases:
  x=min(releases,key=lambda x:abs(x['popped_ns']-b));free=x['previous_frame_free_ns'];assert free is None or free[0]<=free[1]<=x['loop_started_ns']
  points=[a]+[max(a,min(b,v)) for v in ((free or [a,a])+[x['loop_started_ns'],x['notification_wait_begin_ns'],x['dequeued_ns'],x['popped_ns']])]+[b]
  assert all(v<=w for v,w in zip(points,points[1:]))
  labels=['before_previous_frame_free','previous_frame_free','free_to_loop','loop_to_notification','notification_wait','native_pop_and_release','release_to_producer_wakeup']
  phases={name:(v-u)/1e6 for name,u,v in zip(labels,points,points[1:])};assert abs(sum(phases.values())-(b-a)/1e6)<1e-7
  overlaps=[z for z in g['records'] if z['begin_ns']<b and z['end_ns']>a]
  row.update(dequeued_refresh=x['refresh'],phases_ms=phases,pop_relative_to_acquire_ms=(x['popped_ns']-b)/1e6,long_presentations=[dict(display_index=z['display_index'],interval_ms=z['interval_ns']/1e6,overlap_ms=(min(b,z['end_ns'])-max(a,z['begin_ns']))/1e6,consumer_stages=z['consumer_stages'],caller_stages=z['caller_stages']) for z in overlaps])
 rows.append(row)
out=dict(result='PASS_COMPLETE_CAPACITY_DEQUEUE_TIME_JOIN',waits=len(rows),matched=sum(x['release_candidates']>0 for x in rows),rows=sorted(rows,key=lambda x:x['wait_ms'],reverse=True),scope='Exact clipped wait partition around consumer timestamps; popped stamp follows release and may race producer wake. Before-free includes ordered rendering/pacing/preparation, not exclusive CPU or scanout proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(dict(waits=out['waits'],matched=out['matched'],largest=out['rows'][:2]),indent=2))
