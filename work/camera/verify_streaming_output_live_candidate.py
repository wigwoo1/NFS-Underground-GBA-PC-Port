import json,sys
from pathlib import Path
p=Path(sys.argv[1]);r=json.loads(p.read_text());assert r['result']=='SMOKE_COMPLETE' and r['error'] is None
rows=r['world_preparation_stage_samples'];count=0;chunks=0;copy_ns=0
assert r['shutdown_evidence']['preparation_service_shutdown']['diagnostic_dropped']==0
for request in rows:
 terminal=request['terminal'];assert terminal[2]=='complete'
 child=terminal[5]['sample_transfer_rows'];parent=request['parent_sample_rows']
 assert len(child)==len(parent)==terminal[3]
 for a,b in zip(child,parent):
  w=a['shared_write'];assert w['streaming_pickle'] and w['native_copy'] and w['chunk_count']>0
  assert w['serialized_ns']==w['copied_ns'] and w['begin_ns']<=w['copied_ns']<=w['descriptor_sent_ns']
  assert w['payload_bytes']==b['shared_read']['payload_bytes'] and 0<=w['copy_elapsed_ns']<=w['copied_ns']-w['begin_ns']
  count+=1;chunks+=w['chunk_count'];copy_ns+=w['copy_elapsed_ns']
out=dict(result='PASS_COMPLETE_LIVE_STREAMING_OUTPUT_SELECTION',requests=len(rows),samples=count,chunks=chunks,native_copy_elapsed_ms=copy_ns/1e6,scope='Every complete child sample uses bounded streaming pickle and matches receiver extent; complete transfer accounting and native owner lifecycle audited separately. Does not prove live pixel fidelity or visible60fps.')
p.with_name(p.stem+'-streaming-output-audit.json').write_text(json.dumps(out,indent=2));print(out)
