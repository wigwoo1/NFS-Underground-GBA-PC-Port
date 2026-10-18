import json,statistics,re
from pathlib import Path
p=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/all-successful-native-starvation-20261010')
raw=re.findall(r'G:[^\r\n]*owned-native-\d+\.json',(p/'source-callback-cycles-pause45.log').read_text())[-1];r=json.loads(Path(raw).read_text());w=r['live_observation_stats']['whole_run_api_intervals'];ledger=w['native_commit_long_intervals'];assert ledger['dropped']==0 and ledger['total']==len(ledger['records'])==6
updates=r['original_update_retention']['complete_original_updates'];assert updates['dropped']==0 and updates['total']==len(updates['records']);assert all(b['refresh']==a['refresh']+1 for a,b in zip(updates['records'],updates['records'][1:]))
s=r['shutdown_evidence'];q=s['preparation_service_shutdown'];assert not q['child_alive'] and not q['preparation_thread_alive'] and q['child_exitcode']==0 and not q['errors'];assert s['native_owner_released'] and s['active_contexts_after_close']==0 and not s['gpu_thread_alive'];assert r['hud_lease_cleanup']['owner_stats']==[0,0,0]
assert len(r['pause_events'])==3
for pause in r['pause_events']:
 assert pause['begin_ns']<=pause['native_pause_ack_ns']<=pause['end_ns']<=pause['native_resume_ack_ns']
 assert pause['buffer_at_begin']['last_committed']==pause['buffer_at_resume']['last_committed']
rows=[]
for x in ledger['records']:
 h=x['prepared']['hud_lease_stages'];a,b,cycles=h['native_callback_profile'];outer=h['callback_outer_cycles'];assert h['callback_begin_ns']<=a<=b<=h['callback_end_ns'];assert outer[1]-outer[0]>=cycles>0
 calls=[]
 for call in x['prepared']['d3d_call_profiles']+[dict(x['prepared']['bundle_transfer_profile'],call='bundle_transfer')]:
  ca,na,nb,cb=[call[k] for k in ['caller_begin_ns','native_begin_ns','native_end_ns','caller_end_ns']];assert ca<=na<=nb<=cb
  calls.append(dict(call=call['call'],native_ms=(nb-na)/1e6,after_native_ms=(cb-nb)/1e6,native_cycles=call['native_cycles']))
 rows.append(dict(index=x['display_index'],generation=x['generation'],gap_ms=x['interval_ns']/1e6,native_callback_ms=(b-a)/1e6,callback_outside_native_ms=((h['callback_end_ns']-h['callback_begin_ns'])-(b-a))/1e6,native_cycles=cycles,outside_native_cycles=outer[1]-outer[0]-cycles,calls=calls))
result=dict(result='PASS_PAUSE45_CALLBACK_BOUNDARY_ACCOUNTING',raw=raw,updates=updates['total'],pauses=3,active_intervals=w['all_successful_native_intervals'],cleanup_verified=True,medians={k:statistics.median(x[k] for x in rows) for k in ['native_callback_ms','callback_outside_native_ms','native_cycles','outside_native_cycles']},rows=rows,scope='6complete retained long intervals and 3pause acknowledgments/held display identities; callback wall/cycles nested, no exclusive GIL/scheduler/GPU causal attribution. Active generations exclude transitions; no physicalscanout or sustained60 qualification.')
(p/'source-callback-cycles-pause45-audit.json').write_text(json.dumps(result,indent=2));print({k:v for k,v in result.items() if k!='rows'})
