"""Measured native callback packet stages and HUD build subset."""
import json,sys
from pathlib import Path
from analyze_native_transaction_long_intervals_candidate import analyze
p=Path(sys.argv[1]);r=json.loads(p.read_text());analyze(r);rows=[]
for e in r['bounded_diagnostic_stats']['whole_run_api_intervals']['native_commit_long_intervals']['records']:
 h=e['prepared']['hud_lease_stages'];a,b,cycles=h['native_callback_profile'];stages=h['source_packet_stages'];split=e['prepared']['hud_build_split']
 assert len(stages)==3 and all(x>=0 for x in stages) and sum(stages)<=b-a
 assert len(split)==8 and split[0] in (0,1) and split[1]<=160
 # Build durations are nested in endpoint HUD stage, not additional callback time.
 assert sum(split[2:7])<=stages[2]
 rows.append(dict(identity=[e['epoch'],e['generation'],e['display_index']],gap_ms=e['interval_ns']/1e6,native_callback_ms=(b-a)/1e6,native_thread_cycles=cycles,packet_stages_ms=dict(background_and_sky=stages[0]/1e6,geometry=stages[1]/1e6,endpoint_hud=stages[2]/1e6),outside_packet_stages_ms=((b-a)-sum(stages))/1e6,hud_cache_reused=bool(split[0]),hud_built_rows=split[1],hud_build_ms=dict(text=split[2]/1e6,copy=split[3]/1e6,decode=split[4]/1e6,post_decode=split[5]/1e6,cache=split[6]/1e6)))
out=dict(result='PASS_NATIVE_CALLBACK_PACKET_HUD_PARTITION',rows=sorted(rows,key=lambda x:x['gap_ms'],reverse=True),scope='All zero-drop long gaps. Native elapsed callback decomposed into three measured packet stages and nonnegative remainder; nested HUD durations not double-counted. Remainder includes validation/input/uninstrumented work and scheduling, not exclusive CPU cause.')
p.with_name(p.stem+'-callback-packet-partition.json').write_text(json.dumps(out,indent=2));print(out['result']);print(json.dumps(out['rows'][:2],indent=2))
