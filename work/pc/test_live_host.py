from pathlib import Path
import subprocess,os,json,hashlib,time,argparse
import numpy as np
from PIL import Image
source=Path(__file__).resolve().parent;root=source.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-live-host-tests';exe=out/'NFSUG-Source-Native-Preview.exe';rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=root/'work/integration-0.state';oracle=base/'NFSUG-android-capture-local/capture-off/frames.raw';env=dict(os.environ)
parser=argparse.ArgumentParser();parser.add_argument('--output-dir',type=Path,default=out);parser.add_argument('--direct-cached',action='store_true');parser.add_argument('--geometry-cache',action='store_true');options=parser.parse_args();out=options.output_dir;exe=out/'NFSUG-Source-Native-Preview.exe'
for key in ['NF_TEST_RACING_OWNED_CAPTURE','NF_LIVE_ROAD_ATTRIBUTES','NF_CAPTURE_MODEL_VIEWS']:env.pop(key,None)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p):sha(p) for p in [rom,state]};assert before[str(rom)]=='53817aec76a623dc2c7782ddf841f89f369aebe5a92a28c9afc69feaf914a593';rows={}
def run(name,frames,extra,race=True,original_oracle=True):
 path=out/f'{name}.json';cmd=[str(exe),'--rom',str(rom),'--hidden','--frames',str(frames),'--report',str(path)]
 if options.geometry_cache:cmd+=['--geometry-cache']
 elif options.direct_cached:cmd+=['--direct-cached']
 if race:cmd+=['--state',str(state),'--script']
 if race and original_oracle:cmd+=['--oracle',str(oracle)]
 cmd+=extra;t=time.monotonic();p=subprocess.run(cmd,env=env,timeout=90);r=json.loads(path.read_text());assert p.returncode==0 and r['exit_code']==0,(name,p.returncode,r);assert r['logic_frames']==frames and r['timing_errors']==0 and r['original_frame_mismatches']==0 and r['present_failures']==0 and r['controller_mapping_checks'] and r['render_thread_owns_gl'] and not r['live_readback'] and r['capture_every_logic_steps']==1;assert r['processed_sequence']==r['final_sequence'],(name,'Final publication not drained');r['process_seconds']=time.monotonic()-t
 if options.geometry_cache:
  stats=r['geometry_cache_statistics'];assert r['geometry_cache_enabled'] and stats[0]==0 and stats[11]==0 and stats[6]<=stats[8] and stats[7]<=stats[8] and stats[9]==0 and stats[8]==32*1024*1024,(name,stats)
  assert r['background_allocations']==r['background_releases'] and r['geometry_allocations']==r['geometry_releases']
  if race:assert stats[1]>0 and stats[2]>0,(name,stats)
 assert r['audio_queue_empty_events']<=r['audio_queue_empty_observations']<=r['audio_queue_observations']
 assert len(r['audio_queue_empty_pcm_frames'])==min(32,r['audio_queue_empty_events'])
 assert len(r['audio_queue_empty_context'])==len(r['audio_queue_empty_pcm_frames'])
 for event,pcm_frame in zip(r['audio_queue_empty_context'],r['audio_queue_empty_pcm_frames']):
  assert event['pcm_frame']==pcm_frame and event['poll_interval_ms']>=0 and 0<=event['previous_queued_buffers']<=8
  assert 0<=event['previous_pending_frames']<=65536 and 0<=event['pending_frames']<=65536
  assert event['previous_pcm_frame']<=pcm_frame
  if not event['previous_poll_valid']:assert event['poll_interval_ms']==0

 assert 0<=r['audio_queue_min_buffers']<=r['audio_queue_max_buffers']<=8
 if '--no-audio' in extra:assert r['audio_queue_observations']==0
 elif r['audio_device_opened']:assert r['audio_queue_observations']>0
 if r['capture_failure_count']:
  assert r['capture_failure_log'] and r['capture_failure_first_frame']==r['capture_failure_log'][0][0],(name,'First capture failure disagrees with event history')
  assert r['capture_failure_last_frame']>=r['capture_failure_log'][-1][0]
 else:assert r['capture_failure_first_frame']==r['capture_failure_last_frame']==0
 rows[name]=r;print(name,json.dumps(r),flush=True);return r
r=run('race-fast',600,['--fast','--no-audio','--audio-dump',str(out/'race-audio.pcm'),'--capture',str(out/'live-native-4k.rgba')]);assert r['single_build_reader'] and r['reader_packet_builds']>0 and r['native_renders']>0 and r['native_presents']>0 and r['fallback_presents']>0 and r['capture_native'];assert r['audio_frames']==443007 and sha(out/'race-audio.pcm')=='eedce61302b062d825e9a26fa1d8399f0a7c29eaf4319e33a3d71eedd40be33e'
raw=(out/'live-native-4k.rgba').read_bytes();assert len(raw)==3840*2160*4;image=np.frombuffer(raw,np.uint8).reshape(2160,3840,4)[::-1].copy();assert image[:,:3240,3].max()==255 and not image[:,3240:].any();Image.fromarray(image).save(out/'live-native-4k.png');assert sha(out/'live-native-4k.png')=='684d891677b6d97bd972aa0079fcd9495118f49c73bcdeb139f8412aab46bff2'
r=run('race-realtime',296,[]);target=296*280896/16777216;assert target<=r['elapsed_seconds']<=target+.15,('Original wall-clock rate not maintained',target,r['elapsed_seconds']);assert r['native_presents']>0 and r['native_renders']>=280 and r['prepared_scenes']>=280 and r['published_frames']>=280 and r['audio_dropped_frames']==0 and r['capture_failure_count']==r['logic_frames']-r['published_frames'] and r['capture_failure_log_count']==min(32,r['capture_failure_count']) and len(r['capture_failure_log'])==r['capture_failure_log_count'] and sum(r['capture_failure_kind_counts'])==r['capture_failure_count'] and r['capture_failure_max_streak']==10 and r['capture_failure_first_frame']==1 and r['capture_failure_last_frame']==10
r=run('capture-gap-short',260,['--fast','--no-audio','--capture-gap-at','120','--capture-gap-steps','6']);assert r['synthetic_capture_gap_at']==120 and r['synthetic_capture_gap_steps']==6 and r['capture_gap_grace_steps']==12 and r['capture_gap_hold_frames']==6 and r['capture_gap_fallback_count']==0 and r['native_presents']>0 and r['capture_failure_count']==16 and r['capture_failure_first_frame']==1 and r['capture_failure_last_frame']==125
r=run('capture-gap-sustained',260,['--fast','--no-audio','--capture-gap-at','120','--capture-gap-steps','15']);assert r['capture_gap_hold_frames']==11 and r['capture_gap_fallback_count']==1 and r['fallback_presents']>0 and r['native_presents']>0 and r['capture_failure_count']==25 and r['capture_failure_first_frame']==1 and r['capture_failure_last_frame']==134
r=run('reset-in-flight',180,['--fast','--no-audio','--reload-after-prepare','--prepare-delay-ms','250']);assert r['reloaded'] and r['stale_rejections']>0 and r['native_renders']>0
r=run('toggle-original',120,['--fast','--no-audio','--toggle-at','60']);assert r['toggled'] and r['native_presents']>0 and r['fallback_presents']>0
r=run('boot-fallback',600,['--fast','--no-audio'],race=False,original_oracle=False);assert r['fallback_presents']>0 and r['capture_failure_count']==600 and r['capture_failure_log_count']==32 and len(r['capture_failure_log'])==32 and r['capture_failure_max_streak']==600 and sum(r['capture_failure_kind_counts'])==600
assert before=={str(p):sha(p) for p in [rom,state]}
receipt=json.loads((out/'live-build-report.json').read_text());assert receipt['exe_sha256']==sha(exe) and receipt['core_sha256']==sha(out/'capture-host.dll')
b=dict(result='PASS_LIVE_SOURCE_NATIVE_HOST_LIMITED_PROTOTYPE',exe_sha256=sha(exe),core_sha256=sha(out/'capture-host.dll'),test_source_sha256=sha(Path(__file__)),build_receipt_sha256=sha(out/'live-build-report.json'),rom_state_sha256=before,original_audio_frames=443007,original_audio_sha256=sha(out/'race-audio.pcm'),source_snapshot_every_logic_steps=1,original_logic_hz=16777216/280896,render_thread_owns_gl=True,no_live_cpu_readback=True,reset_in_flight_rejection_verified=True,original_fallback_verified=True,software_controller_mapping_verified=True,physical_xbox_tested=False,complete_menu_to_race_playthrough=False,full_scene_60fps=False,automatic_save_writes=False,screenshot_sha256=sha(out/'live-native-4k.png'),cases=rows)
(out/'live-test-report.json').write_text(json.dumps(b,indent=2));print(json.dumps({k:v for k,v in b.items() if k!='cases'},indent=2))
