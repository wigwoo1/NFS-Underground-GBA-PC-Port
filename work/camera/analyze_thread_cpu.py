"""CPU counters and wall time; no inference of GPU/OS wait cause."""
from pathlib import Path
import csv,json,statistics,sys
manifest=Path(sys.argv[1]);m=json.loads(manifest.read_text(encoding='utf-8-sig'));prefix=m['prefix'];groups={}
for owner in ['producer','worker']:
 rows=list(csv.DictReader(Path(prefix+'-'+owner+'-cpu.csv').open()))
 for r in rows:
  assert int(r['valid'])==1
  wall=(int(r['end_ns'])-int(r['begin_ns']))/1e6;cpu=(int(r['cpu_end_ns'])-int(r['cpu_begin_ns']))/1e6;cycles=int(r['cycle_end'])-int(r['cycle_begin']);assert wall>=0 and cpu>=0 and cycles>=0
  groups.setdefault(owner+'_'+r['kind'],[]).append(dict(target=float(r['target']),wall_ms=wall,cpu_ms=cpu,cycles=cycles))
result={}
for name,rows in groups.items():
 result[name]=dict(samples=len(rows),total_wall_ms=sum(r['wall_ms'] for r in rows),total_cpu_ms=sum(r['cpu_ms'] for r in rows),median_wall_ms=statistics.median(r['wall_ms'] for r in rows),longest_wall=sorted(rows,key=lambda r:r['wall_ms'],reverse=True)[:5],scope='Thread CPU time has OS accounting quantization; residual wall time cannot distinguish preemption, GPU wait, other waiting, or counter measurement boundaries. Cycles are raw, not converted using guessed CPU frequency.')
Path(prefix+'-cpu-attribution.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

# Nested boundary stages are attribution within submission, never extra CPU work.
split_names=['producer_split_old_extract','producer_split_old_copy','producer_split_new_extract','producer_split_new_copy']
if any(name in groups for name in split_names):
 assert all(name in groups for name in split_names),'Incomplete split-stage profiling'
 totals={r['target']:r for r in groups['producer_submission']};boundaries=[]
 for i,old in enumerate(groups[split_names[0]]):
  target=old['target'];parts=[groups[name][i] for name in split_names]
  assert all(r['target']==target for r in parts)
  total=totals[target];stage_wall=sum(r['wall_ms'] for r in parts)
  assert stage_wall<=total['wall_ms']+.001,'Nested split durations exceed parent'
  boundaries.append(dict(target=target,total_wall_ms=total['wall_ms'],extract_wall_ms=parts[0]['wall_ms']+parts[2]['wall_ms'],copy_wall_ms=parts[1]['wall_ms']+parts[3]['wall_ms'],other_wall_ms=total['wall_ms']-stage_wall,scope='Nested within submission; do not add these stages to aggregate submission cost. CPU accounting remains quantized.'))
 Path(prefix+'-split-cpu-attribution.json').write_text(json.dumps(boundaries,indent=2));print(json.dumps(boundaries,indent=2))
