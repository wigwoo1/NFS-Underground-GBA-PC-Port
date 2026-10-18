"""Bind the bounded sound-reserve fix to controlled, real playback and package tests."""
from pathlib import Path
import hashlib,json
source=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-audio-prefill-live-tests';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
names=['live-build-report.json','live-test-report.json','audio-queue-component-test-report.json','audio-prefill-simulation-report.json','input-ledger-test-report.json','traffic-live-route-test-report.json','logic-audit-test-report.json','traffic-package-report.json'];b,t,c,s,i,r,a,p=[json.loads((out/n).read_text()) for n in names]
old=(out/'before/live_host.c').read_text();current=(source/'live_host.c').read_text();needle=' if(audio_device)for(unsigned i=0;i<8&&audio_count>=2048;i++)';replacement=' /* Start with two blocks to retain one extra block across measured service jitter.\n    Adds 2048/44100 seconds plus producer-step quantization; no rate change. */\n if(audio_device&&(audio_queue_started||audio_count>=4096))for(unsigned i=0;i<8&&audio_count>=2048;i++)';assert old.count(needle)==1 and current==old.replace(needle,replacement)
for n,h in b['source_sha256'].items():assert sha(source/n)==h,n
assert b['exe_sha256']==t['exe_sha256']==r['exe_sha256']==a['exe_sha256']==p['exe_sha256']==sha(out/'NFSUG-Source-Native-Preview.exe')
assert b['core_sha256']==r['core_sha256']==p['core_sha256']==sha(out/'capture-host.dll')
assert s['source_sha256']==c['source_sha256']==sha(source/'live_host.c') and s['script_sha256']==sha(source/'test_audio_prefill_reserve.py') and c['script_sha256']==sha(source/'test_audio_queue_component.py')
assert s['rows']['candidate']['measured_interval']['empty_events']==0 and s['rows']['candidate']['beyond_reserve']['empty_events']>0
assert not r['sampled_audio_queue_empty_observed'] and r['audio_pcm_exact'] and r['original_wall_clock_budget_met'] and r['session']['prepare_failures']==0
assert r['build_receipt_sha256']==sha(out/names[0]) and r['regression_receipt_sha256']==sha(out/names[1])
assert i['audio_start_prefill_frames']==4096 and a['result']=='PASS_CURRENT_HOST_LOGIC_CADENCE_AUDIT' and p['result']=='PASS_TRAFFIC_PREVIEW_PACKAGE_AND_BOTH_LAUNCHERS'
folder=Path(p['folder']);manifest=json.loads((folder/'package-manifest.json').read_text());assert p['manifest_sha256']==sha(folder/'package-manifest.json')
for n,h in manifest['files'].items():assert sha(folder/n)==h,n
assert manifest['audio_start_prefill_frames']==4096 and not manifest['physical_audio_latency_measured']
previous=source.parent.parent/'tryout/NFSUG-Scene-Recovery-Preview-20261017-d8c50b16'
assert sha(previous/'NFSUG-Source-Native-Preview.exe')=='d8c50b161fbda5d51fb7047311954cc68ed7b50518f7c64ea64635a719e8b38b'
assert sha(previous/'capture-host.dll')=='8faddd2f5b09a367014518eaf7da948284ce92d34f1fc3fbfae12d9f67ed2f08'
report=dict(result='VERIFIED_TWO_BLOCK_AUDIO_RESERVE_AND_PLAYABLE_PREVIEW',package=str(folder),exe_sha256=b['exe_sha256'],core_sha256=b['core_sha256'],driver_polls=r['session']['audio_queue_observations'],empty_queue_events=r['session']['audio_queue_empty_events'],minimum_sampled_queued_buffers=r['session']['audio_queue_min_buffers'],maximum_sampled_queued_buffers=r['session']['audio_queue_max_buffers'],original_pcm_exact=True,original_wall_clock_budget_met=True,elapsed_seconds=r['session']['elapsed_seconds'],controlled_added_start_delay_ms=s['controlled_added_start_delay_ms'],physical_sound_latency_measured=False,known_late_capture_gaps=20,prepare_failures=0,full_scene_60fps=False,entire_game_playthrough_verified=False,game_logic='original-timed mGBA core',rough_project_percent=71,previous_playable_exe_core_unchanged=True,receipts={n:sha(out/n) for n in names},script_sha256=sha(Path(__file__)),limits='One local AMD6000-step route, not continuous audible verification or Intel/physical Xbox/full-race validation. Added nominal46.44ms reserve plus producer-step quantization.20 source gaps still hold scenes; no interpolated full-scene60fps claim.')
(out/'audio-prefill-milestone-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
