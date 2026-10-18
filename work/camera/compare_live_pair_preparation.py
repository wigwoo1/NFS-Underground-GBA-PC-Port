"""Observational matched-refresh preparation comparison, never exact-input equivalence."""
import json,sys,statistics
from pathlib import Path
reports=[json.loads(Path(p).read_text()) for p in sys.argv[1:3]]
maps=[];ambiguous_counts=[]
for r in reports:
 m={};ambiguous=set()
 for x in r['world_preparation_stage_samples']:
  k=(x['older'],x['newer'],x['prepared_sample_count'])
  if k in m:ambiguous.add(k)
  m[k]=x
 for k in ambiguous:m.pop(k)
 ambiguous_counts.append(len(ambiguous));maps.append(m)
rows=[]
for key in sorted(maps[0].keys()&maps[1].keys()):
 a,b=(m[key] for m in maps)
 rows.append(dict(pair=list(key),baseline_ms=(a['construct_advance_ns']+a['precompute_ns'])/1e6,candidate_ms=(b['construct_advance_ns']+b['precompute_ns'])/1e6,baseline_construct_ms=a['construct_advance_ns']/1e6,candidate_construct_ms=b['construct_advance_ns']/1e6))
assert rows
summary=dict(excluded_ambiguous_pair_counts=ambiguous_counts,matched_pairs=len(rows),baseline_median_ms=statistics.median(x['baseline_ms'] for x in rows),candidate_median_ms=statistics.median(x['candidate_ms'] for x in rows),median_pair_delta_ms=statistics.median(x['candidate_ms']-x['baseline_ms'] for x in rows))
result=dict(summary=summary,rows=rows,scope='Same older/newer refresh and sample count only; input bytes/planner history not compared. Sequential system loads differ. No causal speedup or physical cadence proof.')
Path(sys.argv[3]).write_text(json.dumps(result,indent=2));print(summary)

