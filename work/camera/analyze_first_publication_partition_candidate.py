"""Exact shared progressive request-to-first-publication elapsed partition."""
import json,sys,statistics
from pathlib import Path
p=Path(sys.argv[1]);r=json.loads(p.read_text());rows=[]
for request in r['world_preparation_stage_samples']:
 if not request['parent_sample_rows']:continue
 child=request['terminal'][5];parent=request['parent_sample_rows'][0];transfer=child['sample_transfer_rows'][0];assert parent['index']==transfer['index']==0
 inp=request['parent_start_timing'];write=inp['input_write'];out=transfer['shared_write'];read=parent['shared_read']
 stamps=[request['started_ns'],inp['pack_begin_ns'],inp['packed_ns'],write['begin_ns'],write['serialized_ns'],write['copied_ns'],write['descriptor_sent_ns'],child['child_started_ns'],child['decoded_ns'],child['initialized_ns'],child['constructed_ns'],transfer['ready_ns'],out['begin_ns'],out['serialized_ns'],out['copied_ns'],min(out['descriptor_sent_ns'],read['begin_ns']),read['begin_ns'],read['copied_ns'],read['decoded_ns'],parent['decoded_ns'],parent['publication_begin_ns'],parent['published_ns']]
 assert stamps==sorted(stamps),(request['older'],request['newer'],stamps)
 ns=[b-a for a,b in zip(stamps,stamps[1:])];assert sum(ns)==parent['published_ns']-request['started_ns']
 names=['dispatch_to_pack','pack','pack_to_write','input_serialize','input_copy','input_descriptor','descriptor_to_child','child_decode','child_initialize','world_construct','source_setup_first_sample','sample_to_write','output_serialize','output_copy','output_descriptor','descriptor_to_parent_read','parent_copy','parent_decode','decode_tail','publication_wait','publish']
 rows.append(dict(older=request['older'],newer=request['newer'],generation=request['generation'],first_publication_ms=sum(ns)/1e6,descriptor_return_overlap_ms=max(0,out['descriptor_sent_ns']-read['begin_ns'])/1e6,input_bytes=write['payload_bytes'],output_bytes=out['payload_bytes'],partition_ms=dict(zip(names,[x/1e6 for x in ns]))))
assert rows
out=dict(result='PASS_REQUEST_FIRST_PUBLICATION_EXACT_PARTITION',requests=len(rows),mean_first_publication_ms=statistics.mean(x['first_publication_ms'] for x in rows),rows=sorted(rows,key=lambda x:x['first_publication_ms'],reverse=True),scope='Parent/child causal boundaries validated and summed exactly; sender descriptor-return timestamp clipped at receiver read begin to account for concurrent pipe send/read. Raw overlap retained separately. Elapsed includes scheduling and synchronous stages; descriptor-to-child not exclusive queue wait. No speedup or visible cadence proof.')
p.with_name(p.stem+'-first-publication-audit.json').write_text(json.dumps(out,indent=2));print(out['result'],len(rows));print(out['rows'][:2])
