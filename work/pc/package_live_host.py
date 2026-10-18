from pathlib import Path
import shutil,json,hashlib,subprocess,time,argparse
source=Path(__file__).resolve().parent;root=source.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-live-host-tests';destination=root/'tryout/NFSUG-Source-Native-Preview-20261015-Assembly-Update'
parser=argparse.ArgumentParser();parser.add_argument('--direct-ram-update',action='store_true');options=parser.parse_args()
if options.direct_ram_update:out=base/'NFSUG-pc-direct-ram-live-tests';destination=root/'tryout/NFSUG-Source-Native-Preview-20261015-RAM-Update'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
build=json.loads((out/'live-build-report.json').read_text());tests=json.loads((out/'live-test-report.json').read_text());assert build['core_kind']==('owned-assembly-direct-ram' if options.direct_ram_update else 'owned-assembly');assert tests['result']=='PASS_LIVE_SOURCE_NATIVE_HOST_LIMITED_PROTOTYPE' and tests['exe_sha256']==build['exe_sha256']==sha(out/'NFSUG-Source-Native-Preview.exe');assert tests['core_sha256']==sha(out/'capture-host.dll') and tests['test_source_sha256']==sha(source/'test_live_host.py')
for name,digest in build['source_sha256'].items():assert sha(source/name)==digest,name
assert destination.parent.resolve()==(root/'tryout').resolve();destination.mkdir(exist_ok=True,parents=True)
profile_name='direct-ram-profile-report.json' if options.direct_ram_update else 'owned-assembly-profile-report.json'
for name in ['NFSUG-Source-Native-Preview.exe','capture-host.dll','libgcc_s_seh-1.dll','libwinpthread-1.dll','live-build-report.json','live-test-report.json',profile_name,'live-native-4k.png']:shutil.copy2(out/name,destination/name)
profile=json.loads((out/profile_name).read_text());assert profile['exe_sha256']==build['exe_sha256']
experiment=base/('NFSUG-pc-direct-ram-core-tests' if options.direct_ram_update else 'NFSUG-pc-owned-assembly-core-tests');parity=json.loads((experiment/'owned-core-test-report.json').read_text());assert parity['core_sha256']==build['core_sha256'] and parity['result']=='PASS_OWNED_ASSEMBLY_CORE_PARITY'
for name in ['owned-core-build-report.json','owned-core-test-report.json','observer-direct-ram.patch' if options.direct_ram_update else 'observer-owned-assembly.patch']:shutil.copy2(experiment/name,destination/name)
if options.direct_ram_update:
 boundary_path=base/'NFSUG-pc-ram-boundary-tests/ram-boundary-report.json';boundary=json.loads(boundary_path.read_text());assert boundary['result']=='PASS_DIRECT_RAM_ACTUAL_CORE_BOUNDARIES' and boundary['candidate_core_sha256']==build['core_sha256'] and boundary['script_sha256']==sha(source/'test_direct_ram_boundaries.py') and boundary['candidate_build_report_sha256']==sha(experiment/'owned-core-build-report.json');shutil.copy2(boundary_path,destination/'ram-boundary-report.json')
reader=json.loads((base/'NFSUG-pc-reader-tests/reader-report.json').read_text())
for name,digest in reader['source_sha256'].items():assert sha(source/name)==digest
shutil.copy2(base/'NFSUG-pc-reader-tests/reader-report.json',destination/'reader-report.json')
for title,race in [('START - Game From Boot.cmd',False),('START - Race Checkpoint.cmd',True)]:
 text='@echo off\r\nsetlocal\r\nset "GAME_ROM=%~dp0..\\..\\..\\Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba"\r\nif not exist "%GAME_ROM%" (\r\n echo The supplied ROM was not found above the project folder.\r\n pause\r\n exit /b 1\r\n)\r\nstart "" "%~dp0NFSUG-Source-Native-Preview.exe" --rom "%GAME_ROM%"'
 if race:text+=' --state "%~dp0..\\..\\work\\integration-0.state"'
 text+=' --report "%~dp0preview-session.json" %*\r\nendlocal\r\n';(destination/title).write_bytes(text.encode('utf-8'))
(destination/'READ ME.txt').write_text('''NFS Underground source-native preview - 15 October 2026 assembly update

Double-click START - Race Checkpoint.cmd to try driving immediately.
START - Game From Boot.cmd starts at the original game boot screens.
Keep this folder under this project's tryout folder so it can find your ROM.

Keyboard: arrows steer/navigate; Z accelerate/A; X brake/B.
Enter Start; Backspace Select; A left shoulder; S right shoulder.
Xbox: RT/A accelerate; LT/B brake; left stick/D-pad steer.
LB/X left shoulder; RB/Y right shoulder; Menu Start; View Select.
F3 switches native/original display. Space pauses. F1 shows help.
F8 reloads the initial checkpoint when using the checkpoint launcher.
Click the window to resume if switching away paused the game.

This assembly update builds nested capture packets once. It uses a separately
verified packet-assembly variant of the mGBA core; game logic is unchanged. Some stutters
remain; it does not provide smooth 60-fps motion. The earlier preview is
preserved in its original folder.

This is a limited interactive prototype. Original game logic still uses mGBA.
The new source-native renderer draws captured car/world geometry, retained
roads/walls and HUD on a 3840x2160 target with a 3240x2160 game area.
Original boot screens/menus and unavailable native scenes use the original
display. The stable older fallback build has not been replaced.

Native capture currently happens every other game frame (about 30 updates/sec).
Repeated presentation is not smooth 60-fps motion interpolation. That remains
unfinished. Source textures/HUD are original; the 4K texture option is not yet
connected to this renderer. Some geometry pixel differences remain under study.

This preview DOES NOT WRITE GAME SAVES. Progress is lost when it closes.
The supplied ROM/checkpoint and existing saved games remain untouched.
Xbox mapping has software checks; a physical controller has not been tested.
Complete boot-menu-race playthrough and full-game coverage are unverified.

On exit preview-session.json contains a short technical run report.
Use the screenshot and build/test reports here to identify this new renderer.
''')
if options.direct_ram_update:
 p=destination/'READ ME.txt';text=p.read_text();text=text.replace('assembly update','RAM update',1).replace('This assembly update builds nested capture packets once. It uses a separately\nverified packet-assembly variant of the mGBA core; game logic is unchanged. Some stutters','This RAM update copies canonical game RAM directly for native scene capture.\nIt preserves the verified packet assembly and mGBA game logic. The paired\n1200-step test reduced average core processing about 13 percent; some stutters');p.write_text(text)
# Smoke-test the actual network-drive package with a short VISIBLE run. The
# ordinary launchers omit test options and stay interactive until closed.
cmd=[str(destination/'NFSUG-Source-Native-Preview.exe'),'--rom',str(root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba'),'--state',str(root/'work/integration-0.state'),'--frames','120','--script','--no-audio','--oracle',str(base/'NFSUG-android-capture-local/capture-off/frames.raw'),'--report',str(destination/'package-smoke.json')]
subprocess.run(cmd,check=True,timeout=60);smoke=json.loads((destination/'package-smoke.json').read_text());assert smoke['logic_frames']==120 and smoke['native_presents']>0 and smoke['original_frame_mismatches']==0 and smoke['timing_errors']==0 and smoke['present_failures']==0
launcher_tests={}
for name in ['START - Game From Boot.cmd','START - Race Checkpoint.cmd']:
 report=destination/('launcher-boot-test.json' if 'Boot' in name else 'launcher-race-test.json');prior=report.stat().st_mtime_ns if report.exists() else 0
 command=f'cmd.exe /d /s /c ""{destination/name}" --frames 120 --hidden --script --no-audio --report "{report}""'
 subprocess.run(command,cwd=str(out),check=True,timeout=10)
 until=time.monotonic()+30;r=None
 while time.monotonic()<until:
  if report.exists() and report.stat().st_mtime_ns!=prior:
   try:r=json.loads(report.read_text())
   except (ValueError,OSError):pass
   if r:break
  time.sleep(.1)
 assert r and r['exit_code']==0 and r['logic_frames']==120 and r['present_failures']==0,(name,r)
 if 'Checkpoint' in name:assert r['native_presents']>0
 else:assert r['fallback_presents']>0
 launcher_tests[name]=r
b=dict(result='PASS_NETWORK_PACKAGE_VISIBLE_NATIVE_SMOKE',package=str(destination),files_sha256={p.name:sha(p) for p in destination.iterdir() if p.is_file() and p.name!='package-manifest.json'},smoke=smoke,actual_cmd_launchers_tested=launcher_tests,package_script_sha256=sha(Path(__file__)),limited_playable_prototype=True,complete_game_verified=False,full_scene_60fps=False,automatic_save_writes=False)
(destination/'package-manifest.json').write_text(json.dumps(b,indent=2));(out/'package-report.json').write_text(json.dumps(b,indent=2));print(json.dumps({k:v for k,v in b.items() if k not in ['files_sha256','smoke','actual_cmd_launchers_tested']},indent=2))
