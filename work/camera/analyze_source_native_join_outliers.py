import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text()); rows=[]
for interval in sorted(r['world_preparation_stage_samples'],key=lambda x:x['child_stages']['precompute_ns'],reverse=True)[:5]:
 c=interval['child_stages']; samples=[]
 for s in c.get('sample_timings',[]):
  samples.append(dict(alpha=s['alpha'],wall_ms=s['wall_ns']/1e6,source=[dict(name=t['name'],wall_ms=t['wall_ns']/1e6,cycles=t.get('thread_cycles'),cpu_ns=t.get('thread_cpu_ns')) for t in s.get('source_sample_stages',[])],assembly=[dict(name=t['name'],wall_ms=t['wall_ns']/1e6,cycles=t.get('thread_cycles'),join=t.get('frame_join_trace')) for t in s.get('assembly_stages',[]) if t['wall_ns']>5_000_000 or t['name']=='immutable_frame_join']))
 rows.append(dict(older=interval['older'],newer=interval['newer'],precompute_ms=c['precompute_ns']/1e6,whole_child_cpu_ms=c['child_thread_cpu_ns']/1e6,samples=samples))
output=Path(sys.argv[2]);output.write_text(json.dumps(dict(result='MEASURED',intervals=rows,scope='Nested source and assembly wall/CPU-cycle evidence. Coarse zero CPU is not zero work; no exclusive cause or scanout claim.'),indent=2))
for row in rows[:2]:
 print(row['older'],row['newer'],row['precompute_ms'],[(s['alpha'],[(t['name'],t['wall_ms'],t['cycles']) for t in s['source'] if t['wall_ms']>5]) for s in row['samples']])