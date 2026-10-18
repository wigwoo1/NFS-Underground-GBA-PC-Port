"""Separate manual-test preview; does not promote the candidate as a completed port."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,uuid
root=Path('Y:/CODEX/NFSUG-Native-PC-Port');base=Path('C:/NFSUG-Workspace');out=base/'NFSUG-pc-audio-duration-tests';source=root/'work/pc';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
names=['live-build-report.json','report.json','logic-audit-test-report.json','live-test-report.json','duration-input-ledger-report.json','duration-serial-report.json','duration-route-report.json']
b,c,a,t,i,serial,first=[json.loads((out/name).read_text()) for name in names]
assert b['exe_sha256']==a['exe_sha256']==t['exe_sha256']==serial['exe_sha256']==sha(out/'NFSUG-Source-Native-Preview.exe')
assert b['core_sha256']==a['core_sha256']==t['core_sha256']==serial['core_sha256']==sha(out/'capture-host.dll')
for name,digest in b['source_sha256'].items():assert sha(source/name)==digest,name
assert c['source_sha256']==a['source_sha256']==i['source_sha256']==sha(source/'live_host.c')
assert c['rows']['candidate']['measured']['empty_events']==0 and c['rows']['candidate']['extreme_stall']['empty_events']>0
assert serial['original_wall_clock_budget_met'] and serial['pcm_exact']
s=serial['session'];assert s['audio_queue_empty_events']==0 and s['audio_dropped_frames']==0 and s['audio_duration_valid']>0
assert s['capture_gap_fallback_count']==0 and s['capture_failure_count']==10 and s['prepare_failures']==s['present_failures']==s['timing_errors']==0
assert t['result']=='PASS_LIVE_SOURCE_NATIVE_HOST_LIMITED_PROTOTYPE' and a['original_native_display_hashes_exact'] and i['result']=='PASS_AUDIO_DURATION_INPUT_LEDGER_AND_PCM_PULL'
previous=root/'tryout/NFSUG-Traffic-Preview-20261017-65c23dca-3fa8f2ad';old=json.loads((previous/'package-manifest.json').read_text())
protected={previous/name:sha(previous/name) for name in old['files']}
for path,digest in protected.items():assert digest==old['files'][path.name],path
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=root/'work/integration-0.state';protected.update({rom:sha(rom),state:sha(state)})
dest=root/('tryout/NFSUG-Audio-Duration-Test-20261017-'+b['exe_sha256'][:8]+'-'+b['core_sha256'][:8])
if dest.exists():
 assert not (dest/'package-manifest.json').exists() and not (dest/'launcher-smoke-report.json').exists(),'Preserve completed package'
 allowed=set(names+['NFSUG-Source-Native-Preview.exe','capture-host.dll','libgcc_s_seh-1.dll','libwinpthread-1.dll','START - Game From Boot.cmd','START - Race Checkpoint.cmd','race-checkpoint.state','READ ME.txt'])
 assert all(path.is_file() and path.name in allowed for path in dest.iterdir()),'Unexpected partial-package content'
 for name in ['NFSUG-Source-Native-Preview.exe','capture-host.dll']:
  if (dest/name).exists():assert sha(dest/name)==sha(out/name)
else:dest.mkdir()
for name in ['NFSUG-Source-Native-Preview.exe','capture-host.dll']:shutil.copyfile(out/name,dest/name)
for name in ['libgcc_s_seh-1.dll','libwinpthread-1.dll','START - Game From Boot.cmd','START - Race Checkpoint.cmd']:shutil.copyfile(previous/name,dest/name)
shutil.copyfile(state,dest/'race-checkpoint.state')
for name in names:shutil.copyfile(out/name,dest/name)
(dest/'READ ME.txt').write_text('''NFS Underground - AUDIO DURATION TEST PREVIEW

Double-click START - Race Checkpoint.cmd to drive from the supplied checkpoint.
START - Game From Boot.cmd starts the menus. This is an experimental test build.
For another PC, copy this WHOLE folder to a local drive and place your supplied
ROM beside the launchers, retaining its original filename. The ROM is not bundled.
The launchers also find the supplied ROM above the project when used in Y:/CODEX.

Controls: F1 help; F3 Original/native DISPLAY comparison; Space pause;
F8 checkpoint reload. Xbox: RT/A accelerate, LT/B brake, stick/D-pad steer,
Menu Start, View Select. Keyboard: Z accelerate, X brake, arrows steer,
Enter Start, Backspace Select. Close normally to write preview-session.json.
Automatic game-save writes are disabled. Existing builds/saves are preserved.

What changed: partial audio refills use remaining sound duration rather than
number of queued buffers. The existing two-block startup reserve is retained.
Game logic still runs through mGBA at its original timing. The 3D scene renderer
is native; menus and unsupported displays use the original framebuffer.
This is not a full native rewrite of game logic or a finished 60-fps port.

Verified locally: exact original PCM and logic clocks; native 4K framebuffer;
6000-step varied driving route with no late source fallback or dropped PCM;
zero sampled empty queues in the serial run; boot/reset/mode/input regressions.
A separate run overlapping another graphics test observed three empty-queue
polls. Neither those polls nor a clean serial run measure audible continuity.
Please check music stutter, tearing and resolution fallback on your Intel PC.
Physical Xbox, a complete race, visible smooth 60-fps full-scene/sky motion and
Intel/NVIDIA performance remain unverified. No guaranteed stutter-fix claim.

Textures are ORIGINAL. Re-imagined AI artwork and Remastered SUPIR artwork,
and their three-choice texture menu, are not available in this preview yet.
4K rendering resolution does not mean the artwork has been regenerated.

If reporting a problem, include preview-session.json and whether this folder
was run from the network drive or a local drive. The old preview and stable
synchronized 4K fallback have not been replaced.
''',encoding='utf-8')
def quote(value):
 assert not any(c in value for c in '"\r\n%');return '"'+value+'"'
env=dict(os.environ);windows=env['SYSTEMROOT'];env['PATH']=str(Path(windows)/'System32')+';'+windows
smokes={}
for name,race in [('START - Game From Boot.cmd',False),('START - Race Checkpoint.cmd',True)]:
 report=out/('duration-package-'+('race' if race else 'boot')+'-'+uuid.uuid4().hex[:8]+'.json');args=[str(dest/name),'--hidden','--frames','66','--script','--fast','--no-audio','--report',str(report)]
 if race:args+=['--oracle',str(base/'NFSUG-android-capture-local/capture-off/frames.raw')]
 command='cmd.exe /d /v:off /s /c "'+' '.join(quote(arg) for arg in args)+'"'
 subprocess.run(command,cwd=str(base),env=env,check=True,stdin=subprocess.DEVNULL,timeout=45)
 row=json.loads(report.read_text());assert row['exit_code']==0 and row['logic_frames']==66 and row['timing_errors']==row['original_frame_mismatches']==row['present_failures']==0
 assert row['geometry_cache_enabled'] and row['background_allocations']==row['background_releases'] and row['geometry_allocations']==row['geometry_releases']
 assert row['native_renders']>0 if race else row['fallback_presents']>0
 smokes[name]=row
(dest/'launcher-smoke-report.json').write_text(json.dumps(smokes,indent=2),encoding='utf-8')
assert all(sha(path)==digest for path,digest in protected.items())
manifest=dict(kind='experimental-audio-duration-manual-test-preview',game_logic='mGBA original timing',renderer='native scene renderer with original framebuffer fallback',rom_included=False,stable_release_promoted=False,full_scene_60fps=False,physical_audible_quality_verified=False,intel_user_device_verified=False,physical_xbox_verified=False,automatic_save_writes=False,serial_sampled_empty_events=0,overlapping_test_sampled_empty_events=first['session']['audio_queue_empty_events'],texture_mode='Original only',enhanced_texture_modes_available=False,clean_path_launcher_tests=True,files={path.name:sha(path) for path in dest.iterdir() if path.is_file()})
(dest/'package-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
for name,digest in manifest['files'].items():assert sha(dest/name)==digest,name
report=dict(result='PASS_AUDIO_DURATION_MANUAL_TEST_PACKAGE_LAUNCHERS',folder=str(dest),race_launcher=str(dest/'START - Race Checkpoint.cmd'),boot_launcher=str(dest/'START - Game From Boot.cmd'),exe_sha256=b['exe_sha256'],core_sha256=b['core_sha256'],manifest_sha256=sha(dest/'package-manifest.json'),previous_package_rom_state_unchanged=True,source_sha256=sha(Path(__file__)),stable_release_promoted=False,full_scene_60fps=False)
(out/'duration-package-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
