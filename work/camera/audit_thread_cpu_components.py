from pathlib import Path
import csv,json,collections
p=Path(__file__).resolve().parent;r=json.loads((p/'threaded-racing-motion-audit.json').read_text());groups=[]
for owner in ('producer','worker'):
 rows=list(csv.DictReader(Path(r['prefix']+'-'+owner+'-cpu.csv').open()));by=collections.defaultdict(list)
 for row in rows:assert int(row['valid'])==1;by[row['kind']].append(row)
 for kind,items in by.items():
  wall=sum(int(x['end_ns'])-int(x['begin_ns']) for x in items);cpu=sum(int(x['cpu_end_ns'])-int(x['cpu_begin_ns']) for x in items)
  groups.append(dict(owner=owner,kind=kind,count=len(items),wall_ms=wall/1e6,cpu_ms=cpu/1e6,cpu_wall_ratio=cpu/wall if wall else 0))
out=dict(result='THREAD_CPU_COMPONENT_EVIDENCE',live_gate_result=r['result'],prefix=r['prefix'],groups=groups,scope='Thread CPU counters include timer granularity; wall minus CPU can include GPU/driver waits and scheduling. No causal scheduler or live60fps proof.')
(p/'thread-cpu-component-audit.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
