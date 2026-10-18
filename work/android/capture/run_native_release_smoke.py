from pathlib import Path
import subprocess,json,hashlib,time
b=Path(r'C:\NFSUG-Workspace');r=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');app=b/'NFSUG-android-local/app-native-experiment-release';adb=b/'android-tools/sdk/platform-tools/adb.exe'
def run(args,timeout=45):return subprocess.run([str(adb),'-s','emulator-5556',*map(str,args)],check=True,capture_output=True,timeout=timeout).stdout
def exists(name):return subprocess.run([str(adb),'-s','emulator-5556','shell','run-as','org.codex.nfsugpreview','test','-f','files/'+name],capture_output=True).returncode==0
def sha(data):return hashlib.sha256(data).hexdigest()
for i in range(60):
 try:
  if run(['shell','getprop','sys.boot_completed'],5).strip()==b'1':break
 except (subprocess.CalledProcessError,subprocess.TimeoutExpired):pass
 time.sleep(1)
else:raise RuntimeError('Owned emulator not ready')
assert run(['emu','avd','name']).decode().splitlines()[0].strip()=='NFSUG_API30'
a=json.loads((app/'apk-build-report.json').read_text());assert sha(Path(a['apk']).read_bytes())==a['sha256'];restore=r/'tryout/NFSUG-Android-Core-Preview-20261015-LifecycleUpdate/NFSUG-Android-Core-Preview.apk';restore_sha='8c901a522176955ec8592a961766dead26ab7275de81a0e01a3b1de790bc383f';assert sha(restore.read_bytes())==restore_sha
names=['game.gba','battery.sav','battery.sav.bak','battery.sav.new','resume.state','resume.state.bak','resume.state.new'];backups={};run(['shell','am','force-stop','org.codex.nfsugpreview'])
for name in names:backups[name]=run(['exec-out','run-as','org.codex.nfsugpreview','cat','files/'+name]) if exists(name) else None
try:
 run(['install','-r',a['apk']]);run(['logcat','-c']);launch=run(['shell','am','start','-W','-n','org.codex.nfsugpreview/.PreviewActivity']).decode();assert 'Status: ok' in launch;time.sleep(3);log=run(['logcat','-d','-v','threadtime']);(app/'release-launch-logcat.txt').write_bytes(log);assert b'FATAL EXCEPTION' not in log and b'Unable to instantiate activity' not in log;(app/'release-launch.txt').write_text(launch);assert 'org.codex.nfsugpreview/.PreviewActivity' in run(['shell','dumpsys','activity','activities']).decode();print('Release APK installed and ordinary Activity launched',flush=True)
finally:
 run(['shell','am','force-stop','org.codex.nfsugpreview'])
 for name,data in backups.items():
  current=run(['exec-out','run-as','org.codex.nfsugpreview','cat','files/'+name]) if exists(name) else None
  if data is None:
   if current is not None:run(['shell','run-as','org.codex.nfsugpreview','rm','-f','files/'+name])
  elif current!=data:
   local=app/('temporary-original-'+name);local.write_bytes(data);temp='/data/local/tmp/nfsug-private-restore-'+name
   try:run(['push',local,temp]);run(['shell','run-as','org.codex.nfsugpreview','cp',temp,'files/'+name])
   finally:run(['shell','rm','-f',temp]);local.unlink()
  assert (run(['exec-out','run-as','org.codex.nfsugpreview','cat','files/'+name]) if exists(name) else None)==data,name
 run(['install','-r',restore]);path=run(['shell','pm','path','org.codex.nfsugpreview']).decode().strip().split(':',1)[1];assert run(['shell','sha256sum',path]).decode().split()[0]==restore_sha;run(['emu','kill']);print('Normal ROM/save contents preserved; published APK restored and hash verified',flush=True)
report=dict(result='PASS_RELEASE_EMULATOR_LAUNCH',apk_sha256=a['sha256'],ordinary_activity=True,normal_rom_present=backups['game.gba'] is not None,normal_rom_save_bytes_preserved=True,published_apk_restored=True,gameplay_verified_by_this_smoke_test=False,physical_device=False);(app/'release-launch-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
