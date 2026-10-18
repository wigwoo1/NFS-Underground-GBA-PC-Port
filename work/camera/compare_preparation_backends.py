"""Same-duration live clock comparison, without claiming causality from two runs."""
import json,sys
from pathlib import Path
rows=[]
for name in sys.argv[1:]:
 p=Path(name);r=json.loads(p.read_text());t=r['timing'];samples=r['world_preparation_stage_samples'];process=r.get('process_preparation_enabled',False)
 row=dict(shared_process_output=r.get('shared_process_output_enabled',False),report=str(p),backend='process' if process else 'thread',updates=r['original_updates'],scenes=r['owned_scene_submissions'],presentations=r['presentations'],wall_seconds=t['wall_seconds'],simulated_seconds=t['simulated_seconds'],clock_ratio=t['simulated_seconds']/t['wall_seconds'],prepared_pairs=len(samples))
 if process:row['child_stage_total_ms']={k:sum(x['child_stages'][k] for x in samples)/1e6 for k in samples[0]['child_stages']}
 else:row['preparation_total_ms']={k:sum(x[k] for x in samples)/1e6 for k in ('construct_advance_ns','precompute_ns','construct_thread_cpu_ns','precompute_thread_cpu_ns')}
 rows.append(row)
result=dict(scope='sequential bounded live runs; no sustained60fps proof or isolated backend causality',runs=rows)
Path('work/camera/prototype-runs/preparation-backend-comparison.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
