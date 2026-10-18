"""Compare recorded preparation at the same refresh pair, without assuming identical inputs."""
import json,sys
from pathlib import Path
rows=[]
for name in sys.argv[1:4]:
 r=json.loads(Path(name).read_text());p=next(x for x in r['world_preparation_stage_samples'] if x['older']==10331 and x['newer']==10336)
 samples=[]
 for s in p['sample_timings']:
  samples.append(dict(alpha=s['alpha'],world_ms=next(x['wall_ns']/1e6 for x in s['source_sample_stages'] if x['name']=='world_sample'),world_cycles=next(x['thread_cycles'] for x in s['source_sample_stages'] if x['name']=='world_sample'),assembly=[dict(name=x['name'],wall_ms=x['wall_ns']/1e6,cycles=x['thread_cycles'],geometry_records=x.get('geometry_records'),count=x.get('count')) for x in s['assembly_stages']]))
 rows.append(dict(report=name,prepared_sample_count=p['prepared_sample_count'],construct_ms=p['construct_advance_ns']/1e6,precompute_ms=p['precompute_ns']/1e6,precompute_cycles=p['precompute_thread_cycles'],samples=samples))
wait=json.loads(Path('work/camera/visibility-gc-wait-stalls.json').read_text())['largest'][0]
out=dict(result='PASS_RECORDED_PAIR_COMPARISON',pair=[10331,10336],runs=rows,largest_gap={k:wait[k] for k in ['display_index','gap_ms','parts','wait_ms','entered_late_ms']},scope='Same epoch refresh numbers do not prove equal graph/input/workload. Alpha/sample counts and stage counts exposed; no exclusive cause or physical cadence proof.')
Path('work/camera/same-pair-preparation-comparison.json').write_text(json.dumps(out,indent=2));print([(x['prepared_sample_count'],x['construct_ms'],x['precompute_ms'],x['precompute_cycles'],[s['alpha'] for s in x['samples']]) for x in rows])
