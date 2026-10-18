import json,statistics
from pathlib import Path
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791517842433748000.json').read_text());rows=r['producer_cycle_samples'];assert len(rows)==r['producer_retention']['total_records'];rows=rows[len(r['capture_batch_checks']):];native=[];copies=[];outside=[]
for row in rows:
 boundaries=row.get('frame_read_boundaries',[])
 if len(boundaries)!=1 or not boundaries[0].get('batch'):continue
 b=boundaries[0];inside=b['native'][1]-b['native'][0];native.append(inside);copy=row['owned_bytes_copy'];copied=copy['completed_ns']-copy['started_ns'];copies.append(copied);outside.append(row['stages']['frame_read_ns']-inside-copied)
out=dict(result='MEASURED_RETAINED_BATCH_READ_COST',retained_samples=len(native),median_native_batch_ms=statistics.median(native)/1e6,median_owned_bytes_copy_ms=statistics.median(copies)/1e6,median_other_frame_stage_ms=statistics.median(outside)/1e6,scope='Retained window excludes initial parity checks in this run; wall durations, uncontrolled scheduling. Native batch still invokes query+read; no improvement proof.')
Path('work/camera/prototype-runs/sky-reuse-batch-cost-20261008.json').write_text(json.dumps(out,indent=2));print(out)

