from pathlib import Path
import json,sys
r=json.loads(Path(sys.argv[1]).read_text());ledger=r['bounded_diagnostic_stats']['whole_run_api_intervals']['native_commit_long_intervals'];assert ledger['dropped']==0
operations=[]
for request in r['world_preparation_stage_samples']:
 s=request['parent_start_timing'];assert s['pack_begin_ns']<=s['packed_ns']<=s['sent_ns']
 for name,a,b in [('input_pack',s['pack_begin_ns'],s['packed_ns']),('input_send',s['packed_ns'],s['sent_ns'])]:operations.append((name,a,b))
 w=s.get('input_write')
 if w is not None:
  assert s['packed_ns']<=w['begin_ns']<=w['serialized_ns']<=w['copied_ns']<=w['descriptor_sent_ns']<=s['sent_ns']
  operations.pop()
  for name,a,b in [('input_serialize',w['begin_ns'],w['serialized_ns']),('input_shared_copy',w['serialized_ns'],w['copied_ns']),('input_descriptor_send',w['copied_ns'],w['descriptor_sent_ns'])]:operations.append((name,a,b))
 for p in request['parent_sample_rows']:
  shared=p['shared_read'];assert shared['begin_ns']<=shared['copied_ns']<=shared['decoded_ns']<=p['received_ns']<=p['decoded_ns']<=p['publication_begin_ns']<=p['published_ns']<=p['ack_sent_ns']
  for name,a,b in [('shared_copy',shared['begin_ns'],shared['copied_ns']),('shared_unpickle',shared['copied_ns'],shared['decoded_ns']),('frame_decode',p['received_ns'],p['decoded_ns']),('private_publication',p['publication_begin_ns'],p['published_ns']),('ack_send',p['published_ns'],p['ack_sent_ns'])]:operations.append((name,a,b))
def union(intervals):
 end=total=0
 for a,b in sorted(intervals):
  if b>end:total+=b-max(a,end);end=b
 return total
rows=[];seen=set()
for entry in ledger['records']:
 for d in (entry['prepared']['renderer_dispatch'],entry['caller_stages'].get('hud_prefetch_dispatch')):
  if d is None:continue
  p=d['input_poll_profile'];key=(p['begin_ns'],p['end_ns']);
  if key in seen:continue
  seen.add(key);a,b=key;matches={};intervals=[]
  for name,c,e in operations:
   lo=max(a,c);hi=min(b,e)
   if lo<hi:matches.setdefault(name,[]).append((lo,hi));intervals.append((lo,hi))
  overlap=union(intervals);assert overlap<=b-a
  rows.append(dict(index=entry['display_index'],kind=d['kind'],observed_poll_ms=(b-a)/1e6,native_poll_ms=p['native_ns']/1e6,parent_operation_overlap_ms=overlap/1e6,by_operation_ms={name:union(v)/1e6 for name,v in matches.items()},uncovered_ms=(b-a-overlap)/1e6))
assert rows
out=dict(result='PASS_RETAINED_PARENT_INPUT_OVERLAP_ACCOUNTING',raw=sys.argv[1],parent_operations=len(operations),unique_poll_windows=len(rows),rows=sorted(rows,key=lambda x:x['observed_poll_ms'],reverse=True),scope='Complete retained long native interval ledger, correlated with retained parent protocol stages. Union avoids double-counting. Parent operation ranges contain possible wait/scheduling; overlap is correlation, not GIL ownership or exclusive CPU cause. Uncovered time does not rule out unrecorded parent work.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out['result']);print(json.dumps(out['rows'][:4],indent=2))
