import json
from pathlib import Path
a=json.loads(Path('compact_gap_live_audit.json').read_text());r=json.loads(Path(a['source']).read_text())
rows=[]
for worst in a['records'][:8]:
    pair=worst['source_pair']
    candidates=[s for s in r['world_preparation_stage_samples'] if [s['older'],s['newer']]==pair
                and s['started_ns']<=worst['take_end_ns'] and s['completed_ns']>=worst['take_begin_ns']]
    item=dict(frame=worst,matching_requests=len(candidates))
    if len(candidates)==1:
        s=candidates[0];t=s['terminal'][-1]
        assert t['decoded_ns']<=t['initialized_ns']<=t['constructed_ns']<=t['child_finished_ns']
        item['request']=dict(pair=pair,generation=s['generation'],queue_ms=s['queue_wait_ns']/1e6,
            decode_ms=(t['decoded_ns']-t['child_started_ns'])/1e6,
            construct_ms=(t['constructed_ns']-t['initialized_ns'])/1e6,
            samples=[dict(index=x['index'],prepare_ms=x['prepare_since_ack_ns']/1e6,
                          send_ms=x['send_ns']/1e6,ack_wait_ms=x['ack_wait_ns']/1e6,
                          ready_ns=x['ready_ns']) for x in t['sample_transfer_rows']])
        # A collection overlap is an association. Never sum overlaps across stages.
        trace=t['child_gc_trace'];assert trace['dropped']==0
        item['child_gc_during_take']=[dict(generation=e['generation'],duration_ms=(e['end_ns']-e['start_ns'])/1e6)
            for e in trace['rows'] if max(e['start_ns'],worst['take_begin_ns'])<min(e['end_ns'],worst['take_end_ns'])]
    rows.append(item)
out=dict(rows=rows,scope='Exact source-pair and overlapping request join; fraction does not yet prove consumed prepared sample index. Child times are caller envelopes, not exclusive CPU costs. No sustained60 claim.')
Path('compact_pair_preparation.json').write_text(json.dumps(out,indent=2))
for x in rows[:3]:print(json.dumps(x))
