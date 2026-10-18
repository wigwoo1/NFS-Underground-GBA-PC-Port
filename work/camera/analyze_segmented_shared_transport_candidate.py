"""Summarize bounded process telemetry without claiming exclusive CPU or scanout."""
import json,sys,statistics
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());rows=r['world_preparation_stage_samples']
assert r['process_preparation_enabled'] and r['shared_process_output_enabled'] and rows
keys=('input_pack_ns','request_send_ns','response_wait_ns','response_receive_ns','child_trace_receive_ns','parent_output_decode_ns','ipc_and_prepare_ns')
stats={}
for key in keys:
 values=[row[key]/1e6 for row in rows];assert all(value>=0 for value in values)
 stats[key]=dict(median_ms=statistics.median(values),max_ms=max(values),rows=len(values))
for label,source,a,b in [('mapping_read','shared_read','begin_ns','end_ns'),('mapping_write','shared_write','begin_ns','end_ns')]:
 values=[]
 for row in rows:
  item=row[source] if source=='shared_read' else row['child_stages'][source]
  assert item is not None and item[b]>=item[a]
  values.append((item[b]-item[a])/1e6)
 stats[label]=dict(median_ms=statistics.median(values),max_ms=max(values),rows=len(values))
shutdown=r['shutdown_evidence']['preparation_service_shutdown']
assert shutdown['child_alive'] is False and shutdown['child_exitcode']==0 and shutdown['forced_termination'] is False and shutdown['connection_closed'] is True and shutdown['shared_mapping_closed'] is True
out=dict(result='PASS_SHARED_TRANSPORT_STAGE_AND_SHUTDOWN_AUDIT',stats=stats,retention=r['preparation_retention'],shutdown=shutdown,scope='Retained bounded stage window only; request wait overlaps child work. Descriptor receive excludes mapping copy. No causal performance, full-run quantile, timing or scanout claim.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
