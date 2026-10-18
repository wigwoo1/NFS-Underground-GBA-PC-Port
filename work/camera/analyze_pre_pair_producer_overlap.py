"""Attribute pre-pair gaps using interval-clipped original updates and source work."""
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());ledger=r['bounded_diagnostic_stats']['whole_run_api_intervals']['native_commit_long_intervals'];assert ledger['dropped']==0
assert r['producer_retention']['dropped_records']==0
worst=max(ledger['records'],key=lambda e:e['interval_ns']);start=worst['begin_ns'];end=worst['caller_stages']['pair_begin_ns'];assert end>start
spans=[];records=[]
for name,rows in [('original_update',r['original_update_samples']),('source_producer',r['producer_cycle_samples'])]:
 for row in rows:
  a,b=row['started_ns'],row['completed_ns'];assert b>=a
  lo,hi=max(start,a),min(end,b)
  if hi<=lo:continue
  spans.append((lo,hi));entry=dict(kind=name,refresh=row['refresh'],whole_ms=(b-a)/1e6,overlap_ms=(hi-lo)/1e6,thread_cycles=row.get('thread_cycles'))
  if name=='source_producer':entry.update(stages_ms={k:v/1e6 for k,v in row['stages'].items()},native_capture_detail_available=any(p.get('native') for p in row['frame_read_boundaries']))
  records.append(entry)
merged=[]
for a,b in sorted(spans):
 if merged and a<=merged[-1][1]:merged[-1][1]=max(b,merged[-1][1])
 else:merged.append([a,b])
covered=sum(b-a for a,b in merged)
out=dict(result='PASS_PREPAIR_INTERVAL_OVERLAP',identity=[worst['epoch'],worst['generation'],worst['display_index']],prepair_ms=(end-start)/1e6,observed_union_ms=covered/1e6,uncovered_ms=(end-start-covered)/1e6,records=records,scope='Interval overlap of original-update and source-producer records; merged union avoids double counting. Uncovered is unattributed, not proven idle. Raw cycles not converted to time; no exclusive scheduler/GIL/CPU cause.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print('prepair',out['prepair_ms'],'covered',out['observed_union_ms'],'unattributed',out['uncovered_ms'])
