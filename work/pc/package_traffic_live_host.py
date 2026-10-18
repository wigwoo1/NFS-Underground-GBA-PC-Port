"""Package a separately gated traffic preview; preserve all prior packages."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,uuid
source=Path(__file__).resolve().parent;root=source.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-traffic-live-host-tests';core=base/'NFSUG-pc-traffic-rotation-draw-camera-core';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
parser=argparse.ArgumentParser();parser.add_argument('--output-dir',type=Path,default=out);out=parser.parse_args().output_dir
files={'live-build-report.json':out/'live-build-report.json','live-test-report.json':out/'live-test-report.json','logic-audit-test-report.json':out/'logic-audit-test-report.json','input-ledger-test-report.json':out/'input-ledger-test-report.json','traffic-live-route-test-report.json':out/'traffic-live-route-test-report.json','traffic-draw-camera-build-report.json':core/'traffic-draw-camera-build-report.json','traffic-draw-camera-core-test-report.json':core/'traffic-draw-camera-core-test-report.json','traffic-draw-camera-milestone-report.json':core/'traffic-draw-camera-milestone-report.json'}
b,t,a,i,r,c,p,m=[json.loads(files[n].read_text()) for n in files]
reserve=json.loads((out/'audio-prefill-simulation-report.json').read_text());component=json.loads((out/'audio-queue-component-test-report.json').read_text())
assert reserve['result']=='VERIFIED_TWO_BLOCK_RESERVE_MEASURED_STALL_AND_LATENCY' and reserve['source_sha256']==component['source_sha256']==sha(source/'live_host.c')
assert reserve['script_sha256']==sha(source/'test_audio_prefill_reserve.py') and component['script_sha256']==sha(source/'test_audio_queue_component.py')
assert reserve['rows']['candidate']['measured_interval']['empty_events']==0 and reserve['rows']['candidate']['beyond_reserve']['empty_events']>0 and i['audio_start_prefill_frames']==4096
files.update({'audio-prefill-simulation-report.json':out/'audio-prefill-simulation-report.json','audio-queue-component-test-report.json':out/'audio-queue-component-test-report.json'})
assert b['core_kind']=='guarded-traffic-draw-camera-candidate' and r['result']=='VERIFIED_TRAFFIC_LIVE_ROUTE_LIMITED_PREVIEW'
assert t['result']=='PASS_LIVE_SOURCE_NATIVE_HOST_LIMITED_PROTOTYPE' and a['result']=='PASS_CURRENT_HOST_LOGIC_CADENCE_AUDIT'
assert r['original_wall_clock_budget_met'] and r['audio_pcm_exact'] and not r['sampled_audio_queue_empty_observed'] and r['late_capture_misses']==20
assert r['all_known_capture_gaps_held_without_gba_fallback'] and r['session']['prepare_failures']==r['session']['present_failures']==0
assert b['exe_sha256']==t['exe_sha256']==a['exe_sha256']==r['exe_sha256']==sha(out/'NFSUG-Source-Native-Preview.exe')
assert b['core_sha256']==t['core_sha256']==a['core_sha256']==r['core_sha256']==c['core_sha256']==p['core_sha256']==m['core_sha256']==sha(out/'capture-host.dll')
assert r['build_receipt_sha256']==sha(files['live-build-report.json']) and r['regression_receipt_sha256']==sha(files['live-test-report.json'])
assert t['test_source_sha256']==sha(source/'test_live_host.py') and a['test_sha256']==sha(source/'test_logic_audit.py') and i['script_sha256']==sha(source/'test_traffic_live_inputs.py') and r['script_sha256']==sha(source/'test_traffic_live_route.py')
for n,h in b['source_sha256'].items():assert sha(source/n)==h,n
for n,h in c['maintained_source_sha256'].items():assert sha(source/n)==h,n
for row in t['cases'].values():assert row['background_allocations']==row['background_releases'] and row['geometry_allocations']==row['geometry_releases']
destination=root/'tryout'/('NFSUG-Traffic-Preview-20261017-'+b['exe_sha256'][:8]+'-'+b['core_sha256'][:8]);destination.mkdir(parents=True,exist_ok=True)
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=root/'work/integration-0.state';before={str(p):sha(p) for p in [rom,state]}
for n in ['NFSUG-Source-Native-Preview.exe','capture-host.dll','libgcc_s_seh-1.dll','libwinpthread-1.dll']:
 if (destination/n).exists():assert sha(destination/n)==sha(out/n)
 else:shutil.copy2(out/n,destination/n)
if (destination/'race-checkpoint.state').exists():assert sha(destination/'race-checkpoint.state')==sha(state)
else:shutil.copy2(state,destination/'race-checkpoint.state')
previous=root/'tryout/NFSUG-Scene-Recovery-Preview-20261017-d8c50b16';previous_manifest=json.loads((previous/'package-manifest.json').read_text())
for n in ['START - Game From Boot.cmd','START - Race Checkpoint.cmd']:
 assert sha(previous/n)==previous_manifest['files'][n];shutil.copy2(previous/n,destination/n)
(destination/'READ ME.txt').write_text('NFS Underground - experimental traffic renderer preview\n\nDouble-click START - Race Checkpoint.cmd to drive, or START - Game From Boot.cmd\nfor menus. F1 controls; F3 original/native comparison; Space pause; F8 checkpoint reload.\nXbox: RT/A accelerate, LT/B brake, left stick/D-pad steer, Menu Start, View Select.\nClose normally to write preview-session.json. Automatic save writes are disabled.\n\nThis build connects the improved traffic capture to the playable native renderer.\nEmpty projected triangles no longer reject an otherwise valid native scene.\nThe tested varied route had20 late source gaps instead of799. During those brief\ngaps the previous native scene is held, so short freezes can remain.\nSound starts with two2048-frame blocks to absorb measured delivery stalls.\nThis adds about50ms startup sound delay in a controlled test; physical sound\nlatency has not been measured. The tested6000-step run observed no empty queues.\nThe same original-timed mGBA core still runs game logic. This is not a standalone\ngame-logic rewrite. Presentation repeats do not establish smooth60-fps motion.\nThe sky/full scene are not yet verified at60-fps motion; source textures remain original.\n\nTests cover a6,000-step scripted local AMD native-render/audio run and existing\n4K, reset, original/native toggle, startup and software input regressions.\nThey do not prove a completed race, Intel/NVIDIA performance, physical Xbox input\nor continuous audible output between sampled queue checks.\n\nROM is not included. This folder finds the supplied ROM at the project parent or\nbeside the launcher using its original filename. For another PC, copy the whole\nfolder locally and put your supplied ROM beside the launchers.\nOlder previews and the stable synchronized4K fallback are preserved.\nDeveloper recipe: work/pc/build_traffic_live_host.py, test_live_host.py --geometry-cache,\ntest_logic_audit.py --geometry-cache, test_traffic_live_inputs.py,\ntest_traffic_live_route.py and package_traffic_live_host.py.\n')
def quote(value):
 assert not any(c in value for c in '\"\r\n%');return '\"'+value+'\"'
smokes={}
for title,race in [('START - Game From Boot.cmd',False),('START - Race Checkpoint.cmd',True)]:
 report=out/('traffic-package-'+('race' if race else 'boot')+'-'+uuid.uuid4().hex[:8]+'.json');argv=[str(destination/title),'--hidden','--frames','66','--script','--fast','--no-audio','--report',str(report)]
 if race:argv+=['--oracle',str(base/'NFSUG-android-capture-local/capture-off/frames.raw')]
 command='cmd.exe /d /v:off /s /c "'+' '.join(quote(v) for v in argv)+'"';subprocess.run(command,cwd=str(out),check=True,stdin=subprocess.DEVNULL,timeout=45);row=json.loads(report.read_text())
 assert row['exit_code']==0 and row['logic_frames']==66 and row['timing_errors']==row['original_frame_mismatches']==row['present_failures']==0 and row['geometry_cache_enabled']
 assert row['background_allocations']==row['background_releases'] and row['geometry_allocations']==row['geometry_releases']
 assert row['native_renders']>0 if race else row['fallback_presents']>0
 smokes[title]=row
assert before=={str(p):sha(p) for p in [rom,state]}
for name,path in files.items():shutil.copy2(path,destination/name)
(destination/'launcher-smoke-report.json').write_text(json.dumps(smokes,indent=2));manifest=dict(kind='experimental-traffic-source-native-preview',game_logic='mGBA original timing',rom_included=False,known_late_source_gaps_tested_route=20,full_scene_60fps=False,physical_xbox_tested=False,intel_nvidia_tested=False,automatic_save_writes=False,audio_start_prefill_frames=4096,controlled_added_audio_start_delay_ms=50,physical_audio_latency_measured=False,files={p.name:sha(p) for p in destination.iterdir() if p.is_file() and p.name not in ['package-manifest.json','preview-session.json']});(destination/'package-manifest.json').write_text(json.dumps(manifest,indent=2))
for n,h in manifest['files'].items():assert sha(destination/n)==h,n
report=dict(result='PASS_TRAFFIC_PREVIEW_PACKAGE_AND_BOTH_LAUNCHERS',folder=str(destination),race_launcher=str(destination/'START - Race Checkpoint.cmd'),boot_launcher=str(destination/'START - Game From Boot.cmd'),exe_sha256=b['exe_sha256'],core_sha256=b['core_sha256'],manifest_sha256=sha(destination/'package-manifest.json'),rom_state_unchanged=True,previous_launcher_files_unchanged=True,source_sha256=sha(Path(__file__)),full_scene_60fps=False)
(out/'traffic-package-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
