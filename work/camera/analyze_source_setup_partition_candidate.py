import json,sys
from pathlib import Path
from analyze_native_transaction_long_intervals_candidate import analyze
p=Path(sys.argv[1]);r=json.loads(p.read_text());analyze(r);rows=[]
for e in r['bounded_diagnostic_stats']['whole_run_api_intervals']['native_commit_long_intervals']['records']:
 prepared=e['prepared'];a,b,c,d=prepared['source_setup_ticks'];start,end,*_=prepared['hud_lease_stages']['native_callback_profile']
 assert start<=a<=b<=c<=d<=end
 spans=[a-start,b-a,c-b,d-c,end-d];assert sum(spans)==end-start
 rows.append(dict(identity=[e['epoch'],e['generation'],e['display_index']],gap_ms=e['interval_ns']/1e6,native_callback_ms=(end-start)/1e6,partition_ms=dict(zip(['callback_to_main','frame_hud_input','geometry_setup','render_state_backdrop','sky_geometry_hud_and_return'],[x/1e6 for x in spans]))))
out=dict(result='PASS_SOURCE_SETUP_NATIVE_PARTITION',rows=sorted(rows,key=lambda x:x['gap_ms'],reverse=True),scope='Complete retained long commit gaps and nested monotonic native setup timestamps; exact elapsed sum, includes scheduling. No exclusive CPU or60fps claim.')
p.with_name(p.stem+'-source-setup-partition.json').write_text(json.dumps(out,indent=2));print(json.dumps(out['rows'][:3],indent=2))
