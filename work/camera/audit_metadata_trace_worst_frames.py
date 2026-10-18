import json,re
from pathlib import Path
audit=json.loads(Path('borrowed_metadata30_audit.json').read_text());report=json.loads(Path(audit['source']).read_text())
raw=Path(audit['log']).read_bytes();log=raw.decode('utf-16' if raw.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig')
parent=json.loads(Path(re.search(r'PARENT_GC_TRACE (.+)',log).group(1).strip()).read_text());assert parent['dropped']==0
d=report['bounded_diagnostic_stats']['whole_run_api_intervals']['deadline_diagnostic'];assert d['dropped']>0
records=sorted(d['records'],key=lambda row:row['gap_ns'] or 0,reverse=True)[:5]
retained_max_ms=records[0]['gap_ns']/1e6
active_max_ms=audit['coverage']['active_intervals']['max_ms']
rows=[]
for sample in records:
    p=sample['prepared'];dispatch=p['renderer_dispatch'];caller=sample['caller_timing'];stages=sample['caller_stages']
    points=[caller['draw_begin_ns'],dispatch['submitted_ns'],dispatch['started_ns'],dispatch['completed_ns'],caller['draw_end_ns']]
    assert points==sorted(points)
    pair=sample['transaction']['commit'][2:4]
    matches=[r for r in report['world_preparation_stage_samples'] if [r['older'],r['newer']]==pair]
    native=p['hud_lease_stages']['native_callback_profile']
    calls=p['borrowed_metadata_calls'];start=dispatch['started_ns'];end=dispatch['completed_ns']
    rows.append(dict(identity=sample['identity'],pair=pair,gap_ms=sample['gap_ns']/1e6,
        draw_parts_ms=dict(zip(('before_submit','queue','job','after_job'),[(b-a)/1e6 for a,b in zip(points,points[1:])])),
        take_ms=(stages['preparation_take_end_ns']-stages['preparation_take_begin_ns'])/1e6,
        source_prepare_ms=p['source_prepare_ns']/1e6,native_callback_ms=(native[1]-native[0])/1e6,
        consumer_stages_ms=[dict(stage=s['stage'],elapsed_ms=s['elapsed_ns']/1e6) for s in p['consumer_stages']],
        metadata_caller_ms=sum(x['end_ns']-x['begin_ns'] for x in calls)/1e6,
        source_pair_match_count=len(matches),
        parent_gc=[dict(generation=e['generation'],same_renderer_thread=e['thread']==dispatch['thread'],duration_ms=(e['end_ns']-e['start_ns'])/1e6)
                   for e in parent['events'] if max(start,e['start_ns'])<min(end,e['end_ns'])]))
out=dict(retained_max_ms=retained_max_ms,active_max_ms=active_max_ms,comparable_maximum=False,rows=rows,diagnostic_dropped=d['dropped'],whole_cadence=audit['coverage']['active_intervals'],scope='Incomplete retained subset; Diagnostic and live-observation maxima differ; these records do not establish the identity of the active-cadence maximum. Nested timings not additive. No complete threshold population or tracing-overhead causation claim.')
Path('metadata_trace_worst_frames.json').write_text(json.dumps(out,indent=2))
for row in rows[:3]:print(json.dumps(row))
