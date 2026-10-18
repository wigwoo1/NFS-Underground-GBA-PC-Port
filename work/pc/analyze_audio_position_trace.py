"""Analyze actual playback-position reserve and owner-thread timing, not audible gaps."""
from pathlib import Path
import csv,hashlib,json,math,statistics
source=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-audio-position-probe';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
b=json.loads((out/'live-build-report.json').read_text());t=json.loads((out/'position-component-report.json').read_text());r=json.loads((out/'traffic-live-route-test-report.json').read_text());csvpath=out/'audio-position-6000.csv'
assert b['core_kind']=='diagnostic-refresh2-audio-position' and b['exe_sha256']==r['exe_sha256']==sha(out/'NFSUG-Source-Native-Preview.exe') and r['position_csv_sha256']==sha(csvpath)
assert b['diagnostic_staged_source_sha256']==t['staged_host_sha256']==sha(out/'live_host_position_probe.c') and t['header_sha256']==sha(source/'audio_position_probe.h')
rows=[];floating={'time','deadline_lag_ms','query_ms','core_total_ms','capture_total_ms','publish_total_ms','lock_total_ms','audio_total_ms','logic_total_ms'}
for row in csv.DictReader(csvpath.open()):
 value={k:float(v) if k in floating else int(v) for k,v in row.items()};assert all(math.isfinite(v) for v in value.values());rows.append(value)
assert len(rows)==12000 and [(x['frame'],x['stage']) for x in rows]==[(i,s) for i in range(1,6001) for s in [0,1]] and all(x['overflow_rows']==0 for x in rows)
assert all(x['produced_frames']==x['submitted_frames']+x['ring_frames'] for x in rows),'Producer/ring/submission diagnostic accounting changed'
assert all(a['time']<=b['time'] for a,b in zip(rows,rows[1:]))
pre=[x for x in rows if x['stage']==0];active=[x for x in pre if x['submitted_frames']>0];valid=[x for x in active if x['position_valid'] and x['remaining_comparable']];events=[]
def context(row):return {k:row[k] for k in ['frame','time','deadline_lag_ms','queued_buffers','ring_frames','produced_frames','submitted_frames','played_frames','remaining_frames','position_type','position_error','position_valid','remaining_comparable','query_ms']}
for event in r['session']['audio_queue_empty_context']:
 matches=[(i,x) for i,x in enumerate(pre) if x['produced_frames']==event['pcm_frame']];entry=dict(legacy_event=event,matched_pre_rows=len(matches))
 if len(matches)==1:
  index,current=matches[0];entry['current']=context(current)
  if index:
   previous=pre[index-1];entry['previous']=context(previous);entry['poll_interval_ms']=(current['time']-previous['time'])*1000;entry['between_polls_phase_ms']={n:current[n+'_total_ms']-previous[n+'_total_ms'] for n in ['core','capture','publish','lock','audio']};entry['previous_remaining_ms']=previous['remaining_frames']/44.1 if previous['remaining_comparable'] else None
 events.append(entry)
def percentile(values,p):
 values=sorted(values);return values[round((len(values)-1)*p)] if values else None
query=[x['query_ms'] for x in rows];reserve=[x['remaining_frames']/44.1 for x in valid];types={str(k):sum(x['position_type']==k for x in rows) for k in sorted({x['position_type'] for x in rows})}
report=dict(result='VERIFIED_AUDIO_POSITION_TRACE',position_rows=len(rows),active_pre_rows=len(active),valid_comparable_pre_rows=len(valid),position_types=types,position_errors=sum(x['position_error']!=0 for x in rows),invalid_or_noncomparable_rows=sum(not x['position_valid'] or not x['remaining_comparable'] for x in rows),reserve_ms=dict(min=min(reserve) if reserve else None,median=statistics.median(reserve) if reserve else None,max=max(reserve) if reserve else None),query_ms=dict(median=statistics.median(query),p99=percentile(query,.99),max=max(query),total=sum(query)),maximum_audio_service_lateness_ms=max(x['deadline_lag_ms'] for x in active),legacy_empty_queue_events=r['session']['audio_queue_empty_events'],empty_events=events,lowest_reserve_pre_rows=[context(x) for x in sorted(valid,key=lambda x:x['remaining_frames'])[:8]],latest_playback_position=context(pre[-1]),original_pcm_exact=r['audio_pcm_exact'],original_wall_clock_budget_met=r['original_wall_clock_budget_met'],late_source_gaps=r['late_capture_misses'],full_scene_60fps=False,rough_project_percent=72,diagnostic_only=True,playback_behavior_changed=False,trace_sha256=sha(csvpath),build_receipt_sha256=sha(out/'live-build-report.json'),live_receipt_sha256=sha(out/'traffic-live-route-test-report.json'),component_receipt_sha256=sha(out/'position-component-report.json'),script_sha256=sha(Path(__file__)),limits='Device-reported position/reserve, not physical audible latency. Probe/API/CSV add overhead. Lateness includes current core work relative to step deadline; it is not itself a missed frame. Phase deltas are measured wall time, not pure CPU time. No causal comparison across different runs.')
(out/'audio-position-analysis.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='lowest_reserve_pre_rows'},indent=2))
