from pathlib import Path
import csv,json,sys,re
p=Path(sys.argv[1]);rows=list(csv.DictReader(Path(str(p)+'-clock-polls.csv').open()));inputs=list(csv.DictReader(Path(str(p)+'-input.csv').open()));assert rows
suppressed=0;present=0;steps=0;last_now=-1;previous=0;origin=None
for row in rows:
 r={k:int(v) for k,v in row.items()};assert r['now_ns']>=last_now;last_now=r['now_ns'];elapsed=r['now_ns']-r['origin_ns'];assert elapsed>=0
 due=elapsed*16777216//(1000000000*280896);latest=elapsed*60//1000000000
 assert due==r['due'] and latest==r['latest_display']
 if origin!=r['origin_ns']:origin=r['origin_ns'];previous=0
 debt=due-previous;assert debt>=0;assert r['simulation_steps']==min(debt,4);assert r['scheduled_simulated']==previous+r['simulation_steps']
 expected=r['scheduled_simulated']==due and latest>=r['next_display_before'];assert r['present']==int(expected)
 assert r['skipped']==(latest-r['next_display_before'] if expected else 0)
 suppressed+=r['scheduled_simulated']<due and latest>=r['next_display_before'];present+=expected;steps+=r['simulation_steps'];previous=r['scheduled_simulated']
first_origin=int(rows[0]['origin_ns'])
live_inputs=[r for r in inputs if int(r['start_ns'])>=first_origin]
warm_inputs=[r for r in inputs if int(r['start_ns'])<first_origin]
assert len(warm_inputs)==40 and all(int(r['end_ns'])<=first_origin for r in warm_inputs)
assert steps==len(live_inputs)
events=[dict(pc=int(a),calls=int(b),wall_ms=int(c)/1e6) for a,b,c in re.findall(r'capture_event pc=(\d+) calls=(\d+) ns=(\d+)',Path(str(p)+'-host.log').read_text())]
out=dict(result='ORIGINAL_CLOCK_POLL_REPLAY_EXACT',prefix=str(p),polls=len(rows),live_original_steps=steps,warmup_original_steps=len(warm_inputs),original_steps=len(inputs),presentation_plans=present,backlog_suppressed_polls=suppressed,ranked_capture_events=sorted(events,key=lambda r:r['wall_ms'],reverse=True)[:8],scope='Exact original clock decision replay; event costs cumulative hook wall time, not isolated CPU or whole-run capture_cost reset counters.')
Path(str(p)+'-clock-poll-analysis.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
