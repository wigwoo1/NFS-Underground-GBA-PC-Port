"""Validate complete bounded slowest-sample anchor and metadata subphases."""
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());ledger=r['preparation_retention']['slow_process_intervals'];assert ledger['dropped']==0 and ledger['total']==len(ledger['records'])
rows=[];checks=0
for request in ledger['records']:
 samples=request['sample_stages'];index=request['anchor_detail_sample_index']
 if not samples:assert index is None;continue
 assert index==max(range(len(samples)),key=lambda i:samples[i]['wall_ns'])
 sample=samples[index]
 for stage in sample['stages']:
  if 'anchor_stages' not in stage:continue
  assert not stage['anchor_stages_truncated'] and stage['anchor_stage_count']==len(stage['anchor_stages'])
  assert not stage['metadata_stages_truncated'] and stage['metadata_stage_count']==len(stage['metadata_stages'])
  last=stage['started_ns'];parts={}
  for name,start,wall,cycles in stage['anchor_stages']:
   assert last<=start<=start+wall<=stage['completed_ns'] and cycles>=0;last=start+wall;checks+=1;parts[name]=wall/1e6
  metadata={};anchor=next((x for x in stage['anchor_stages'] if x[0]=='record_metadata'),None)
  if stage['metadata_stages']:assert anchor is not None
  last=anchor[1] if anchor else 0
  for name,start,wall,cycles in stage['metadata_stages']:
   assert last<=start<=start+wall<=anchor[1]+anchor[2] and cycles>=0;last=start+wall;checks+=1;metadata[name]=wall/1e6
  rows.append(dict(older=request['older'],newer=request['newer'],alpha=sample['alpha'],sample_ms=sample['wall_ns']/1e6,anchor_ms=stage['wall_ns']/1e6,parts_ms=parts,metadata_ms=metadata))
assert checks>0
out=dict(result='PASS_COMPLETE_SELECTED_ANCHOR_DETAIL',requests=ledger['total'],selected_samples=len(rows),phase_checks=checks,rows=sorted(rows,key=lambda x:x['anchor_ms'],reverse=True),scope='Explicitly selected slowest sample per retained slow request; complete ledger zero drops. Elapsed includes scheduling/GC; not exclusive CPU or visible60 proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(dict(requests=out['requests'],phase_checks=checks,largest=out['rows'][:3]),indent=2))
