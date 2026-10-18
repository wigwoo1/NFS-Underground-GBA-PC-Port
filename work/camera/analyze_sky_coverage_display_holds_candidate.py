import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());m=json.loads(Path(sys.argv[2]).read_text());p=r['dxgi_display_progress'];ledger=r['bounded_diagnostic_stats']['whole_run_api_intervals']['native_commit_long_intervals'];assert ledger['dropped']==0 and p['excess_refresh_spans_dropped']==0
rows=[]
for span in p['excess_refresh_spans']:
 old=span['older_native_sample'];new=span['newer_native_sample'];assert old and new
 key=(new['epoch'],new['generation'],new['display_index']);assert list(key[:2])==span['key'] and new['display_index']>old['display_index']
 gaps=[g for g in ledger['records'] if (g['epoch'],g['generation'],g['display_index'])==key]
 assert len(gaps)<=1
 begin=span['start_qpc']*1000000000//span['qpc_frequency'];end=span['end_qpc']*1000000000//span['qpc_frequency']
 pauses=[x for x in r['pause_events'] if x['end_ns']<=begin];last=pauses[-1] if pauses else None
 overlaps=[]
 for c in m['rows']:
  # Retained GPU enqueue/poll ranges only, not all diagnostic replay draws.
  intervals=[(c['coverage_begin_ns'],c['coverage_end_ns']),(c['coverage_poll_begin_ns'],c['coverage_poll_end_ns'])]
  if any(max(begin,a)<min(end,b) for a,b in intervals):overlaps.append([c['epoch'],c['generation'],c['index']])
 info=dict(identity=list(key),reported_hold_ms=(end-begin)/1e6,refresh_advance=span['refresh_advance'],image_advance=span['image_advance'],after_latest_pause_ms=(begin-last['end_ns'])/1e6 if last else None,matching_long_native_gap=bool(gaps),coverage_mask_interval_overlaps=overlaps)
 if gaps:
  g=gaps[0];c=g['caller_stages'];t=g['caller_timing'];info.update(native_gap_ms=g['interval_ns']/1e6,prepare_wait_ms=(c['preparation_take_end_ns']-c['preparation_take_begin_ns'])/1e6,draw_prepare_ms=(t['draw_end_ns']-t['draw_begin_ns'])/1e6,prior_to_draw_ms=(t['draw_begin_ns']-g['begin_ns'])/1e6)
 rows.append(info)
out=dict(result='REPORTED_SKY_DISPLAY_HOLD_ASSOCIATIONS',rows=rows,scope='Reported native identities associated with complete >25ms gap ledger, pause chronology and retained mask enqueue/poll intervals. Missing long gap is below-threshold/unretained detail, not missing display hold. Mask replay runs every frame and remains possible overhead; no exclusive cause or physical scanout claim.')
Path(sys.argv[3]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
