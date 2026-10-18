"""Package only the current, verified maintained source-transfer preview."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,uuid
source=Path(__file__).resolve().parent;root=source.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-maintained-integration';core=base/'NFSUG-pc-source-transfer-core';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
parser=argparse.ArgumentParser();parser.add_argument('--geometry-cache',action='store_true');parser.add_argument('--audio-diagnostics',action='store_true');parser.add_argument('--context-refresh',action='store_true');args=parser.parse_args()
if args.context_refresh:args.geometry_cache=args.audio_diagnostics=True
if args.audio_diagnostics and not args.geometry_cache:parser.error('--audio-diagnostics requires --geometry-cache')
if args.geometry_cache:out=base/'NFSUG-pc-geometry-cache-host';core=base/'NFSUG-pc-geometry-cache-core'
if args.audio_diagnostics:out=base/'NFSUG-pc-audio-queue-tests'
if args.context_refresh:out=base/'NFSUG-pc-model-context-live-tests';core=base/'NFSUG-pc-model-context-handoff'
audio_component=base/'NFSUG-pc-audio-queue-tests/audio-queue-component-test-report.json'
core_build='context-refresh-build-report.json' if args.context_refresh else 'geometry-cache-build-report.json' if args.geometry_cache else 'source-transfer-build-report.json'
core_test='context-refresh-core-test-report.json' if args.context_refresh else 'geometry-cache-core-test-report.json' if args.geometry_cache else 'source-transfer-core-test-report.json'
b=json.loads((out/'live-build-report.json').read_text());t=json.loads((out/'live-test-report.json').read_text());a=json.loads((out/'logic-audit-test-report.json').read_text());c=json.loads((core/core_test).read_text())
assert b['core_kind']==('guarded-model-context-refresh' if args.context_refresh else 'optional-guarded-geometry-cache' if args.geometry_cache else 'maintained-source-transfer') and b['capture_mode_flags']==(['--geometry-cache'] if args.geometry_cache else ['--direct-cached'])
if args.geometry_cache:
 assert c['result']==('PASS_CONTEXT_REFRESH_HANDOFF_CORE_PARITY' if args.context_refresh else 'PASS_GUARDED_GEOMETRY_CACHE_CORE_PARITY') and c['build_report_sha256' if args.context_refresh else 'build_receipt_sha256']==sha(core/core_build)
 if args.audio_diagnostics:
  diagnostic=json.loads((out/'audio-queue-long-test-report.json').read_text());component=json.loads(audio_component.read_text())
  assert diagnostic['result']=='VERIFIED_SAMPLED_AUDIO_QUEUE_OBSERVATIONS' and diagnostic['audio_pcm_exact'] and diagnostic['original_wall_clock_budget_met']
  assert diagnostic['exe_sha256']==b['exe_sha256'] and diagnostic['core_sha256']==b['core_sha256'] and diagnostic['regression_receipt_sha256']==sha(out/'live-test-report.json') and diagnostic['build_receipt_sha256']==sha(out/'live-build-report.json')
  assert diagnostic['script_sha256']==sha(source/'test_audio_queue_long.py')
  if args.context_refresh:
   proof=json.loads((core/'probe/context-refresh-probe-report.json').read_text())
   assert proof['result']=='PASS_CONTEXT_HANDOFF_RECOVERS_SCENE_458' and proof['core_sha256']==b['core_sha256'] and proof['maintained_probe_sha256']==sha(source/'probe_model_context_refresh.py') and diagnostic['no_capture_failures_after_startup']
  assert component['result']=='PASS_REAL_HOST_AUDIO_QUEUE_COMPONENT' and component['source_sha256']==sha(source/'live_host.c') and component['script_sha256']==sha(source/'test_audio_queue_component.py')
 else:
  profile=json.loads((out/'geometry-cache-profile-report.json').read_text())
  assert profile['result']=='PASS_GUARDED_CACHE_HOST_ABBA_PROFILE' and profile['exe_sha256']==b['exe_sha256'] and profile['core_sha256']==b['core_sha256'] and profile['test_receipt_sha256']==sha(out/'live-test-report.json') and profile['script_sha256']==sha(source/'profile_geometry_cache_host.py')
assert t['result']=='PASS_LIVE_SOURCE_NATIVE_HOST_LIMITED_PROTOTYPE' and a['result']=='PASS_CURRENT_HOST_LOGIC_CADENCE_AUDIT'
assert b['exe_sha256']==t['exe_sha256']==a['exe_sha256']==sha(out/'NFSUG-Source-Native-Preview.exe')
assert b['core_sha256']==t['core_sha256']==c['core_sha256']==sha(out/'capture-host.dll')
for n,h in b['source_sha256'].items():assert sha(source/n)==h,n
for n,h in c['maintained_source_sha256' if args.geometry_cache else 'source_sha256'].items():assert sha(source/n)==h,n
assert t['test_source_sha256']==sha(source/'test_live_host.py') and a['test_sha256']==sha(source/'test_logic_audit.py')
for name,r in t['cases'].items():
 assert r['direct_cached_capture'] and r['reader_scratch_bytes']==r['reader_copied_bytes']==0,(name,r)
 assert r['background_allocations']==r['background_releases'] and r['geometry_allocations']==r['geometry_releases']
destination=root/'tryout'/(('NFSUG-Scene-Recovery-Preview-20261017-' if args.context_refresh else 'NFSUG-Audio-Diagnostic-Preview-20261017-' if args.audio_diagnostics else 'NFSUG-Cache-Preview-20261017-' if args.geometry_cache else 'NFSUG-Maintained-Preview-20261017-')+b['exe_sha256'][:8]);destination.mkdir(exist_ok=True,parents=True)
for n in ['NFSUG-Source-Native-Preview.exe','capture-host.dll','libgcc_s_seh-1.dll','libwinpthread-1.dll']:
 if (destination/n).exists():assert sha(destination/n)==sha(out/n),n
 else:shutil.copy2(out/n,destination/n)
state=root/'work/integration-0.state';rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';before={str(p):sha(p) for p in [rom,state]}
if (destination/'race-checkpoint.state').exists():assert sha(destination/'race-checkpoint.state')==sha(state)
else:shutil.copy2(state,destination/'race-checkpoint.state')
for title,race in [('START - Game From Boot.cmd',False),('START - Race Checkpoint.cmd',True)]:
 text='@echo off\nsetlocal\npushd "%~dp0"\nset "NFSUG_ROM_FILE=%~dp0Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba"\nif not exist "%NFSUG_ROM_FILE%" set "NFSUG_ROM_FILE=%~dp0..\\..\\..\\Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba"\nif not exist "%NFSUG_ROM_FILE%" (\n echo Put the supplied ROM beside this launcher using its original filename.\n pause\n popd\n exit /b 1\n)\n"%~dp0NFSUG-Source-Native-Preview.exe" --direct-cached --rom "%NFSUG_ROM_FILE%"'
 if args.geometry_cache:text=text.replace('--direct-cached','--geometry-cache')
 if race:text+=' --state "%~dp0race-checkpoint.state"'
 text+=' --report "%~dp0preview-session.json" %*\nset "NFSUG_RUN_EXIT=%errorlevel%"\nif not "%NFSUG_RUN_EXIT%"=="0" (\n echo Preview error. See preview-session.json here.\n pause\n)\npopd\nexit /b %NFSUG_RUN_EXIT%\n';(destination/title).write_text(text)
(destination/'READ ME.txt').write_text('NFS Underground maintained source-native preview\n\nDouble-click START - Race Checkpoint.cmd to drive, or START - Game From Boot.cmd for menus.\nF1 controls; F3 original/native comparison; Space pause; F8 reload initial checkpoint.\nXbox RT/A accelerate, LT/B brake, left stick/D-pad steer, Menu Start, View Select.\nClose normally to save preview-session.json for diagnosis. Game saves are not written.\n\nUses original-timed mGBA game logic and the experimental source-native renderer.\nCapture runs each logic step. Repeated presentation is not 60-fps motion interpolation.\nFull-race timing/correctness, physical Xbox input, Intel/NVIDIA performance, complete\ntexture replacements and Android release are still unverified or unfinished.\nSource textures/HUD are original; native 4K target does not imply 4K source textures.\n\nROM is not included. This folder finds the supplied ROM at the project parent, or\nbeside the launcher using its original filename. Copy the whole folder locally on\nanother PC and put your ROM beside it. The original checkpoint and older packages\nare preserved. Rebuild through work/pc/rebuild_source_transfer_preview.py.\n')
if args.geometry_cache:
 readme=destination/'READ ME.txt';text=readme.read_text().replace('maintained source-native preview','guarded-cache source-native preview')
 text=text.replace('Rebuild through work/pc/rebuild_source_transfer_preview.py.', 'This optional preview reuses identical completed geometry with guarded inputs.\nBuild/test recipes: work/pc/build_geometry_cache_core.py, test_geometry_cache_core.py,\nbuild_live_host.py --reuse-scene --source-transfer-core --geometry-cache-core\n--output-dir C:/NFSUG-Workspace/NFSUG-pc-geometry-cache-host.\nThen run test_live_host.py --geometry-cache with that output directory,\ntest_logic_audit.py --geometry-cache with that output directory,\nprofile_geometry_cache_host.py, and package_source_transfer_host.py --geometry-cache.')
 readme.write_text(text)
# Quote only known file paths/flags; reject CMD expansion/quote characters.
def cmd_quote(value):
 assert not any(c in value for c in '\"\r\n%'),value
 return '\"'+value+'\"'
smokes={}
for title,race in [('START - Game From Boot.cmd',False),('START - Race Checkpoint.cmd',True)]:
 report=out/('package-'+('race' if race else 'boot')+'-'+uuid.uuid4().hex[:8]+'.json')
 argv=[str(destination/title),'--hidden','--frames','66','--script','--fast','--no-audio','--report',str(report)]
 if race:argv+=['--oracle',str(base/'NFSUG-android-capture-local/capture-off/frames.raw')]
 command='cmd.exe /d /v:off /s /c "'+' '.join(cmd_quote(v) for v in argv)+'"'
 subprocess.run(command,cwd=str(out),check=True,stdin=subprocess.DEVNULL,timeout=45);r=json.loads(report.read_text())
 assert r['exit_code']==0 and r['logic_frames']==66 and r['timing_errors']==r['original_frame_mismatches']==r['present_failures']==0 and r['direct_cached_capture']
 assert r['reader_scratch_bytes']==r['reader_copied_bytes']==0 and r['background_allocations']==r['background_releases'] and r['geometry_allocations']==r['geometry_releases']
 if args.geometry_cache:
  stats=r['geometry_cache_statistics'];assert r['geometry_cache_enabled'] and stats[0]==stats[9]==stats[11]==0 and stats[6]<=stats[8] and stats[7]<=stats[8]
  if race:assert stats[1]>0
 if race:assert r['native_renders']>0
 else:assert r['fallback_presents']>0
 if args.audio_diagnostics:assert r['audio_queue_observations']==r['audio_queue_empty_observations']==r['audio_queue_empty_events']==0
 smokes[title]=r
assert before=={str(p):sha(p) for p in [rom,state]}
receipts={'live-build-report.json':out/'live-build-report.json','live-test-report.json':out/'live-test-report.json','logic-audit-test-report.json':out/'logic-audit-test-report.json',core_build:core/core_build,core_test:core/core_test,'frame-integration-report.json':base/'NFSUG-pc-source-frame-tests/integration-report.json','reader-direct-test-report.json':base/'NFSUG-pc-source-reader-direct-tests/reader-direct-test-report.json','scene-build-report.json':base/'NFSUG-pc-scene-tests/scene-build-report.json'}
if args.geometry_cache and not args.audio_diagnostics:
 receipts.update({'geometry-cache-profile-report.json':out/'geometry-cache-profile-report.json','geometry-cache-test-report.json':base/'NFSUG-pc-geometry-cache-tests/geometry-cache-test-report.json'})
if args.audio_diagnostics:
 receipts.update({'audio-queue-long-test-report.json':out/'audio-queue-long-test-report.json','audio-queue-component-test-report.json':audio_component,'long-segment-reference-report.json':base/'NFSUG-pc-geometry-cache-host/long-segment-report.json'})
 readme=destination/'READ ME.txt';readme.write_text(readme.read_text()+'\nAudio diagnostic build: no sound fix is claimed. Close normally and share\npreview-session.json to help investigate stuttering on your PC. It records\nsampled playback queue health; it cannot measure the length of audible gaps.\nThis diagnostic binary has its own one-minute audio/timing and regression tests.\nNo new paired speedup benchmark is claimed for this diagnostic binary.\nPackage with package_source_transfer_host.py --geometry-cache --audio-diagnostics.\n')
if args.context_refresh:
 receipts.update({'context-refresh-probe-report.json':core/'probe/context-refresh-probe-report.json','context-handoff-helper-test-report.json':base/'NFSUG-pc-model-context-helper-tests/context-handoff-helper-test-report.json'})
 readme=destination/'READ ME.txt';text=readme.read_text().replace('guarded-cache source-native preview','scene-recovery source-native preview')
 text=text.split('This optional preview')[0]+'\nScene recovery build: corrects five capture failures in the tested segment.\nUses the same audio buffering; sampled queue diagnostics remain enabled.\nClose normally and share preview-session.json if stuttering occurs.\nDeveloper packaging mode: package_source_transfer_host.py --context-refresh.\n'
 readme.write_text(text)
for name,path in receipts.items():shutil.copy2(path,destination/name)
(destination/'launcher-smoke-report.json').write_text(json.dumps(smokes,indent=2))
manifest=dict(kind='scene-recovery-source-native-preview' if args.context_refresh else 'audio-diagnostic-source-native-preview' if args.audio_diagnostics else 'guarded-cache-source-native-preview' if args.geometry_cache else 'maintained-source-native-preview',context_refresh_enabled=args.context_refresh,audio_diagnostics=args.audio_diagnostics,geometry_cache_enabled=args.geometry_cache,full_scene_60fps=False,game_logic='mGBA original timing',rom_included=False,automatic_save_writes=False,physical_xbox_tested=False,intel_nvidia_tested=False,files={p.name:sha(p) for p in destination.iterdir() if p.is_file() and p.name not in ['package-manifest.json','preview-session.json']})
(destination/'package-manifest.json').write_text(json.dumps(manifest,indent=2))
for name,h in manifest['files'].items():assert sha(destination/name)==h,name
report=dict(result='PASS_SCENE_RECOVERY_PREVIEW_PACKAGE_AND_BOTH_LAUNCHERS' if args.context_refresh else 'PASS_AUDIO_DIAGNOSTIC_PREVIEW_PACKAGE_AND_BOTH_LAUNCHERS' if args.audio_diagnostics else 'PASS_GUARDED_CACHE_PREVIEW_PACKAGE_AND_BOTH_LAUNCHERS' if args.geometry_cache else 'PASS_MAINTAINED_PREVIEW_PACKAGE_AND_BOTH_LAUNCHERS',folder=str(destination),race_launcher=str(destination/'START - Race Checkpoint.cmd'),boot_launcher=str(destination/'START - Game From Boot.cmd'),exe_sha256=b['exe_sha256'],core_sha256=b['core_sha256'],manifest_sha256=sha(destination/'package-manifest.json'),rom_state_unchanged=True,full_scene_60fps=False,source_sha256={n:sha(source/n) for n in ['package_source_transfer_host.py','source_transfer_core_api.inc','source_transfer_observer.inc']})
(out/('context-refresh-package-report.json' if args.context_refresh else 'audio-diagnostic-package-report.json' if args.audio_diagnostics else 'geometry-cache-package-report.json' if args.geometry_cache else 'maintained-package-report.json')).write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
