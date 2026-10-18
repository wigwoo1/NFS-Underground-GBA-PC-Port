import json,sys
from pathlib import Path

def read(path):return json.loads(Path(path).read_text())
def input_signature(report):
 return [(row['refresh'],row['keys'],tuple(sorted((row.get('control_snapshot') or {}).items()))) for row in report['inputs']]
def sky_signature(report):
 fields=('epoch','publication','angle','source','asset_origin','serial')
 return [tuple(row.get(k) for k in fields) for row in report['sky_capture_records']]
def validate(report,label):
 assert report['result']=='SMOKE_COMPLETE' and report['error'] is None,(label,report['result'],report['error'])
 for key in ('full_scene_sampling_enabled','background_preparation_enabled','world_samples_precomputed','interpolation_enabled','sky_capture_enabled','sky_interpolation_enabled','sky_continuous_enabled','smoke_steering_enabled'):
  assert report[key],(label,key)
 assert report['timing']['original_clock_hz']==16777216 and report['timing']['cycles_per_update']==280896,label
 assert report['original_updates']>0 and report['owned_scene_submissions']>0 and report['presentations']>0,label
 assert len(report['pause_events'])==3,(label,len(report['pause_events']))
 intervals=report['live_observation_stats']['whole_run_api_intervals']
 long=intervals['long_intervals'];assert intervals['adjacent_successful_intervals']>0 and intervals['excluded_discontinuities']==3,label
 assert long['dropped']==0 and long['total']==len(long['records']), (label,long['total'],long['dropped'],len(long['records']))
 shutdown=report['shutdown_evidence'];prep=shutdown['preparation_service_shutdown']
 assert prep['child_alive'] is False and prep['child_exitcode']==0 and prep['errors']==[],(label,prep)
 assert shutdown['gpu_thread_alive'] is False and shutdown['native_owner_released'] is True,label
 assert shutdown['active_contexts_after_close']==0 and shutdown['retained_scene_count']==0 and shutdown['pending_scene_count']==0,label
 return {'updates':report['original_updates'],'scene_submissions':report['owned_scene_submissions'],'presentations':report['presentations'],'pause_generations':len(report['pause_events']),'sky_captures':len(report['sky_capture_records']),'intervals':{'n':intervals['adjacent_successful_intervals'],'mean_ms':intervals['mean_ms'],'max_ms':intervals['max_ms'],'over25':intervals['over_25ms'],'over33':intervals['over_33_333ms'],'over50':intervals['over_50ms'],'long_rows':long['total'],'dropped_long_rows':long['dropped']}}
base=read(sys.argv[1]);cand=read(sys.argv[2]);bs=validate(base,'baseline');cs=validate(cand,'candidate')
assert base['original_updates']==cand['original_updates']
assert abs(base['timing']['simulated_seconds']-cand['timing']['simulated_seconds'])<1e-9
assert input_signature(base)==input_signature(cand),'Original update/control sequence differs'
assert len(base['sky_capture_records'])>0 and sky_signature(base)==sky_signature(cand),'Sky source identities differ'
assert len(base['final_ram'])==len(cand['final_ram']) and all(base['final_ram'][k]['sha256']==cand['final_ram'][k]['sha256'] for k in base['final_ram']),'Final emulated RAM differs'
bi=bs['intervals'];ci=cs['intervals'];improved=(ci['over25']<=bi['over25'] and ci['over33']<=bi['over33'] and ci['over50']<=bi['over50'] and ci['max_ms']<bi['max_ms'] and ci['mean_ms']<=bi['mean_ms'] and (ci['over25']<bi['over25'] or ci['over33']<bi['over33'] or ci['over50']<bi['over50'] or ci['mean_ms']<bi['mean_ms']))
out={'result':'PASS_MATCHED_TEXTURE_BACKDROP_LIVE_PAIR','pair_integrity':'PASS_IDENTICAL_ORIGINAL_CLOCK_INPUT_SKY_RAM_PAUSES_AND_CLEANUP','baseline':bs,'candidate':cs,'cadence_improved':improved,'smooth_60fps_verified':False,'scope':'Matched original-clock full-scene runs only. Relative cadence improvement is not a 60-fps certification; physical display scanout remains unverified.'}
path=Path(sys.argv[3]);path.write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))