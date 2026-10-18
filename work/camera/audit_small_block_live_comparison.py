import json,re,sys
from pathlib import Path
from verify_pause_native_segment_coverage import verify
p=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/all-successful-native-starvation-20261010');rows=[]
for label,selected in [('baseline',False),('candidate',True)]:
 raw=re.findall(r'G:[^\r\n]*owned-native-\d+\.json',(p/('small-block-live-'+label+'.log')).read_text())[-1];r=json.loads(Path(raw).read_text());coverage=verify(r);(p/('small-block-live-'+label+'-coverage.json')).write_text(json.dumps(coverage,indent=2))
 jobs=r['world_preparation_stage_samples'];assert jobs
 for j in jobs:
  stats=j['terminal'][5]['small_model_block_stats'];assert (stats is not None)==selected
  if selected and not j['history_only']:assert stats['calls']>0
 updates=r['original_update_retention']['complete_original_updates'];assert updates['dropped']==0 and updates['total']==len(updates['records']);assert all(b['refresh']==a['refresh']+1 for a,b in zip(updates['records'],updates['records'][1:]));assert all(x['started_ns']>=x['original_deadline_ns'] for x in updates['records'])
 s=r['shutdown_evidence'];q=s['preparation_service_shutdown'];assert not q['child_alive'] and not q['preparation_thread_alive'] and q['child_exitcode']==0 and not q['errors'];assert s['native_owner_released'] and s['active_contexts_after_close']==0 and not s['gpu_thread_alive'];assert r['hud_lease_cleanup']['owner_stats']==[0,0,0]
 a=coverage['active_intervals'];rows.append(dict(variant=label,raw=raw,updates=updates['total'],jobs=len(jobs),selected_verified=True,cleanup_verified=True,pauses=len(r['pause_events']),max_gap_ms=a['max_ms'],over25=a['over25'],over33=a['over33'],over50=a['over50'],skipped=a['skipped_indices_between_successes'],holds=[dict(generation=x['generation'],initial_ms=x['initial_active_hold_ms'],trailing_ms=x['trailing_active_hold_ms']) for x in coverage['segments']],cadence_screen_passed=coverage['cadence_screen_passed']))
assert rows[0]['updates']==rows[1]['updates']
out=dict(result='PASS_SMALL_BLOCK_MATCHED_LIVE_ACCOUNTING',runs=rows,scope='Sequential30s fullscene originaldeadline/noearly/contiguousupdates/pausecoverage/selection/cleanup. Environmentcanvary;25msscreenweakerthan60, no scanout/fullfidelity/physicalXbox proof.')
(p/'small-block-live-comparison.json').write_text(json.dumps(out,indent=2));print(out)
