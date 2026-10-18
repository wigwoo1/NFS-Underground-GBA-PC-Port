"""Classify disjoint recorded stall time without implying exclusive cause."""
import json,sys,statistics,collections
from pathlib import Path
rp,op=map(Path,sys.argv[1:3]);r=json.loads(rp.read_text());gaps=r['largest'];counts=collections.Counter();totals=collections.Counter();rows=[]
for g in gaps:
 parts={x['stage']:x['ms'] for x in g['parts']};dominant=max(parts,key=parts.get);counts[dominant]+=1;totals.update(parts)
 p=g['preparation_readiness'];rows.append(dict(display_index=g['display_index'],gap_ms=g['gap_ms'],dominant_stage=dominant,dominant_ms=parts[dominant],unfinished_ms=p['unfinished_at_acquire_ms'],older=p['older'],newer=p['newer'],parts=parts))
result=dict(result='CLASSIFIED',gaps=len(rows),dominant_stage_counts=dict(counts),summed_disjoint_stage_ms=dict(totals),unfinished_over_one_ms=sum(x['unfinished_ms']>1 for x in rows),unfinished_over_refresh=sum(x['unfinished_ms']>1000/60 for x in rows),median_unfinished_ms=statistics.median(x['unfinished_ms'] for x in rows),worst=rows[:5],scope='Recorded nonpause gaps, disjoint wall stage sums. Stage names include scheduling and contention; not exclusive cause, CPU work or physical presentation proof.')
op.write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
