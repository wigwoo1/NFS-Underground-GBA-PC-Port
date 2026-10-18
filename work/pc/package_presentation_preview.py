"""Package qualified render timing candidate separately from existing previews."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,uuid
root=Path('Y:/CODEX/NFSUG-Native-PC-Port');base=Path('C:/NFSUG-Workspace');out=base/'NFSUG-pc-present-deadline-tests';src=root/'work/pc';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
names=['live-build-report.json','logic-audit-test-report.json','live-test-report.json','deadline-component-report.json','visible-comparison-report.json','deadline-route-report.json']
b,a,t,c,v,long=[json.loads((out/n).read_text()) for n in names]
assert b['exe_sha256']==a['exe_sha256']==t['exe_sha256']==long['exe_sha256']==sha(out/'NFSUG-Source-Native-Preview.exe')
assert b['core_sha256']==a['core_sha256']==t['core_sha256']==long['core_sha256']==sha(out/'capture-host.dll')
for name,digest in b['source_sha256'].items():assert sha(src/name)==digest,name
assert a['original_native_display_hashes_exact'] and t['result']=='PASS_LIVE_SOURCE_NATIVE_HOST_LIMITED_PROTOTYPE'
assert v['result']=='PASS_SEQUENTIAL_VISIBLE_DEADLINE_COMPARISON_LIMITED_SCOPE' and len(v['rows'])==4
assert long['result']=='VERIFIED_DEADLINE_NATIVE_PC_ROUTE_LIMITED_SCOPE' and long['pcm_exact'] and long['original_wall_clock_budget_met']
s=long['session'];assert s['audio_dropped_frames']==s['capture_gap_fallback_count']==0
audio_acceptance=s['audio_queue_empty_events']==0
assert s['capture_failure_count']==10 and s['prepare_failures']==s['present_failures']==s['timing_errors']==0
previous=root/'tryout/NFSUG-Audio-Duration-Test-20261017-b94629be-cf66b6ed';old=json.loads((previous/'package-manifest.json').read_text())
protected={previous/n:d for n,d in old['files'].items()};protected[previous/'package-manifest.json']=sha(previous/'package-manifest.json')
protected.update({Path(p):d for p,d in long['rom_state_sha256'].items()})
assert all(sha(p)==d for p,d in protected.items())
dest=root/('tryout/NFSUG-Presentation-Test-20261017-'+b['exe_sha256'][:8]+'-'+b['core_sha256'][:8]);assert not dest.exists();dest.mkdir()
for name in ['NFSUG-Source-Native-Preview.exe','capture-host.dll']:shutil.copy2(out/name,dest/name)
for name in ['libgcc_s_seh-1.dll','libwinpthread-1.dll','START - Game From Boot.cmd','START - Race Checkpoint.cmd']:shutil.copy2(previous/name,dest/name)
shutil.copy2(root/'work/integration-0.state',dest/'race-checkpoint.state')
for name in names:shutil.copy2(out/name,dest/name)
(dest/'READ ME.txt').write_text('''NFS UNDERGROUND - PRESENTATION TEST PREVIEW

Double-click START - Race Checkpoint.cmd to drive from the checkpoint.
Use START - Game From Boot.cmd to start at the menus.
For another PC, copy this WHOLE folder to a LOCAL drive. Put your supplied ROM
beside the launchers, keeping its original filename. The ROM is not bundled.
The launchers also find the ROM above the project when run from Y:/CODEX.

This build adds a presentation deadline and separates game publication from
display waits. It also includes the earlier audio-duration refill change.
The game still runs through mGBA at the original speed. The scene renderer is
native; menus and unsupported scenes use the original framebuffer fallback.
This is an experimental playable test, not a completed native game-code port.

Controls: F1 help; F3 original/native DISPLAY; Space pause; F8 reload checkpoint.
Xbox: RT/A accelerate, LT/B brake, left stick/D-pad steer, Menu Start, View Select.
Keyboard: Z accelerate, X brake, arrows steer, Enter Start, Backspace Select.
Automatic save writes are disabled. Close normally to save preview-session.json.

Locally verified: native 3840x2160 framebuffer, exact original game-frame/audio
checks, reset and fallback tests, a 6000-step varied route with no late fallback,
no dropped PCM. Three sampled empty audio queue events occurred in this route:
the zero-starvation acceptance check FAILED. Audio continuity is unresolved.
This package is for diagnosis and is not promoted as a stutter fix.
Two short visible comparison
pairs average about16.67ms between host presents. Occasional longer intervals
remain. Repeated presents are not proof of 60 distinct motion frames per second.
Full-scene/sky60fps, absence of tearing, audible continuity, complete-race and
physical Xbox/Intel-PC behavior are not yet verified. No guaranteed stutter fix.

Textures: ORIGINAL only. Re-imagined AI artwork, Remastered SUPIR upscales and
their three-choice texture menu are still planned. 4K rendering is not4K artwork.
Older previews and the stable synchronized4K fallback have not been replaced.

Please try the same track locally on the Intel PC and check music stutter,
tearing and any temporary resolution fallback. Include preview-session.json
with feedback and say whether this was run locally or from the network drive.
''',encoding='utf-8')
env=dict(os.environ);windows=env['SYSTEMROOT'];env['PATH']=str(Path(windows)/'System32')+';'+windows
def quote(s):
 assert not any(c in s for c in '"\r\n%');return '"'+s+'"'
smokes={}
for name,race in [('START - Game From Boot.cmd',False),('START - Race Checkpoint.cmd',True)]:
 report=out/('presentation-package-'+('race' if race else 'boot')+'-'+uuid.uuid4().hex[:8]+'.json')
 args=[str(dest/name),'--hidden','--frames','66','--script','--fast','--no-audio','--report',str(report)]
 if race:args+=['--oracle',str(base/'NFSUG-android-capture-local/capture-off/frames.raw')]
 cmd='cmd.exe /d /v:off /s /c "'+' '.join(quote(arg) for arg in args)+'"'
 subprocess.run(cmd,cwd=str(base),env=env,check=True,stdin=subprocess.DEVNULL,timeout=45)
 r=json.loads(report.read_text());assert r['exit_code']==0 and r['logic_frames']==66 and r['timing_errors']==r['original_frame_mismatches']==r['present_failures']==0
 assert r['geometry_cache_enabled'] and r['processed_sequence']==r['final_sequence']
 assert r['background_allocations']==r['background_releases'] and r['geometry_allocations']==r['geometry_releases']
 assert r['native_renders']>0 if race else r['fallback_presents']>0
 smokes[name]=r
(dest/'launcher-smoke-report.json').write_text(json.dumps(smokes,indent=2),encoding='utf-8')
assert all(sha(p)==d for p,d in protected.items())
manifest=dict(kind='experimental-native-presentation-diagnostic-preview-audio-gate-open',game_logic='mGBA original timing',renderer='native scene renderer with original framebuffer fallback',rom_included=False,stable_release_promoted=False,full_scene_60fps=False,tearing_verified=False,physical_audible_quality_verified=False,audio_starvation_acceptance_passed=audio_acceptance,sampled_audio_empty_events=s['audio_queue_empty_events'],intel_user_device_verified=False,physical_xbox_verified=False,automatic_save_writes=False,texture_mode='Original only',enhanced_texture_modes_available=False,clean_path_launcher_tests=True,files={p.name:sha(p) for p in dest.iterdir() if p.is_file()})
(dest/'package-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
for n,d in manifest['files'].items():assert sha(dest/n)==d
report=dict(result='PASS_PORTABLE_DIAGNOSTIC_PACKAGE_LAUNCHERS_AUDIO_GATE_OPEN',folder=str(dest),exe_sha256=b['exe_sha256'],core_sha256=b['core_sha256'],manifest_sha256=sha(dest/'package-manifest.json'),previous_package_rom_state_unchanged=True,audio_starvation_acceptance_passed=audio_acceptance,sampled_audio_empty_events=s['audio_queue_empty_events'],full_scene_60fps=False,stable_release_promoted=False,source_sha256=sha(Path(__file__)))
(out/'presentation-package-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
