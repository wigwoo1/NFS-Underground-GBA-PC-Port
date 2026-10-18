"""Partition actual HUD snapshot waits from source callback elapsed time."""
import json,sys
from pathlib import Path
from analyze_native_transaction_long_intervals_candidate import analyze
p=Path(sys.argv[1]);r=json.loads(p.read_text());analyze(r);rows=[]
for e in r['bounded_diagnostic_stats']['whole_run_api_intervals']['native_commit_long_intervals']['records']:
 prepared=e['prepared'];h=prepared['hud_lease_stages'];t=prepared['hud_transfer']
 a,b,c,d,f,g=[h[k] for k in ['snapshot_begin_ns','snapshot_end_ns','bind_begin_ns','callback_begin_ns','callback_end_ns','release_end_ns']]
 assert a<=b<=c<=d<=f<=g
 spans=[b-a,c-b,d-c,f-d,g-f];assert sum(spans)==g-a
 assert prepared['source_prepare_ns']>=g-a
 item=dict(identity=[e['epoch'],e['generation'],e['display_index']],gap_ms=e['interval_ns']/1e6,snapshot_new=h['snapshot_new'],source_prepare_ms=prepared['source_prepare_ns']/1e6,snapshot_ms=spans[0]/1e6,bind_and_interstage_ms=(spans[1]+spans[2])/1e6,callback_ms=spans[3]/1e6,release_ms=spans[4]/1e6,outer_source_ms=(prepared['source_prepare_ns']-(g-a))/1e6)
 if t is not None:
  assert t['submitted_ns']<=t['started_ns']<=t['completed_ns']<=t['take_end_ns']
  assert a<=t['take_begin_ns']<=t['take_end_ns']<=b
  item.update(hud_ready_before_take=t['ready_before_take'],hud_take_wait_ms=(t['take_end_ns']-t['take_begin_ns'])/1e6,hud_worker_ms=(t['completed_ns']-t['started_ns'])/1e6,hud_prefetch_lead_ms=(t['take_begin_ns']-t['submitted_ns'])/1e6)
 native=h['native_callback_profile'];assert d<=native[0]<=native[1]<=f
 item['native_callback_ms']=(native[1]-native[0])/1e6
 rows.append(item)
out=dict(result='PASS_LONG_GAP_HUD_SOURCE_PARTITION',rows=sorted(rows,key=lambda x:x['gap_ms'],reverse=True),scope='All zero-drop native long gaps; exact source snapshot/bind/callback/release partition and nested HUD worker take ranges. Elapsed ranges include scheduling; prefetch wait not world preparation wait, and no exclusive CPU causation or60fps proof.')
p.with_name(p.stem+'-hud-source-partition.json').write_text(json.dumps(out,indent=2));print(out['result']);print(json.dumps(out['rows'][:3],indent=2))
