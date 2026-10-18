"""Analyze actual producer and worker clocks; never infer 60fps from clock grid alone."""
from pathlib import Path
import csv,json,statistics,sys
p=Path(__file__).resolve().parent
report=json.loads((p/'threaded-motion-complete-test.json').read_text())
prefix=Path(sys.argv[1]) if len(sys.argv)>1 else Path(report['prefix'])
def rows(suffix):return list(csv.DictReader(Path(str(prefix)+suffix).open()))
def distribution(values):
 values=sorted(values)
 return dict(count=len(values),median_ms=statistics.median(values)/1e6,p95_ms=values[min(len(values)-1,int(.95*len(values)))]/1e6,maximum_ms=max(values)/1e6) if values else dict(count=0)
producer=rows('-producer.csv');worker=rows('-worker.csv');inputs=rows('-input.csv')
keys=lambda r:(r['epoch'],round(float(r['target']),8))
lookup={keys(r):r for r in producer}
by_kind={}
for kind in sorted(set(r['frame_kind'] for r in worker)):
 group=[r for r in worker if r['frame_kind']==kind]
 captures=[lookup[keys(r)] for r in group if keys(r) in lookup]
 by_kind[kind]=dict(draw=distribution([int(r['draw_end_ns'])-int(r['start_ns']) for r in group]),capture=distribution([int(r['copy_end_ns'])-int(r['begin_ns']) for r in captures]),capture_to_draw=distribution([int(r['start_ns'])-int(lookup[keys(r)]['begin_ns']) for r in group if keys(r) in lookup]),deadline_lateness=distribution([max(0,int(r['commit_begin_ns'])-int(r['deadline_ns'])) for r in group]),late_commits=sum(int(r['committed'])==1 and int(r['commit_begin_ns'])>int(r['deadline_ns'])+1000000 for r in group))
commits=[r for r in worker if r['committed']=='1']
slots=[round((float(r['target'])-int(r['source_base'])+8)*280896*60/16777216) for r in commits]
assert all(b>a for a,b in zip(slots,slots[1:])), 'Non-monotonic source publication'
missing=[dict(after=a,before=b,missed=b-a-1) for a,b in zip(slots,slots[1:]) if b>a+1]
result=dict(prefix=str(prefix),by_kind=by_kind,original_tick=distribution([int(r['end_ns'])-int(r['start_ns']) for r in inputs]),committed=len(commits),interior_missing_slots=sum(x['missed'] for x in missing),largest_slot_gap=max((x['missed'] for x in missing),default=0),first_slot=slots[0] if slots else None,last_slot=slots[-1] if slots else None,scope='Observed wall clocks include scheduling and validation overhead; draw may include readback/rebind. Capture and draw overlap across threads; do not sum them as sequential frame time. Missing slots contradict sustained60fps in this run.',missing_intervals=missing)
cpu={}
for owner in ['producer','worker']:
 path=Path(str(prefix)+'-'+owner+'-cpu.csv')
 if not path.exists():continue
 records=list(csv.DictReader(path.open()));assert all(r['valid']=='1' for r in records),'Invalid CPU sample'
 cpu[owner]={}
 for kind in sorted(set(r['kind'] for r in records)):
  group=[r for r in records if r['kind']==kind and (kind!='original_tick' or float(r['target'])>=40)]
  wall=sum(int(r['end_ns'])-int(r['begin_ns']) for r in group);used=sum(int(r['cpu_end_ns'])-int(r['cpu_begin_ns']) for r in group);cycles=sum(int(r['cycle_end'])-int(r['cycle_begin']) for r in group)
  cpu[owner][kind]=dict(count=len(group),wall_total_ms=wall/1e6,cpu_total_ms=used/1e6,cpu_to_wall=used/wall if wall else None,cycles=cycles)
 result['cpu_profile']=cpu
result['cpu_scope']='Per-thread CPU counters exclude warmup original ticks; coarse counter resolution makes aggregate ratios more useful than per-frame values. Wall minus CPU includes scheduling, waits and GPU/driver blocking; it is not a direct contention measurement.'
(p/'motion-pipeline-timing.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='missing_intervals'},indent=2))
