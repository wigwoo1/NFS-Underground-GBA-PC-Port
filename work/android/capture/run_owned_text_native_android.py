from pathlib import Path
import subprocess,time,json,hashlib
base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-android-owned-text-ndk-local';adb=base/'android-tools/sdk/platform-tools/adb.exe';root=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');remote='/data/local/tmp/nfsug-owned-text-check'
def run(args,timeout=60):return subprocess.run([str(adb),'-s','emulator-5556',*map(str,args)],check=True,capture_output=True,timeout=timeout).stdout
for i in range(60):
 try:
  if run(['shell','getprop','sys.boot_completed'],5).strip()==b'1':break
 except (subprocess.CalledProcessError,subprocess.TimeoutExpired):pass
 time.sleep(1)
else:raise RuntimeError('Emulator boot failed')
assert run(['emu','avd','name']).decode().splitlines()[0].strip()=='NFSUG_API30'
files={'libnfsug_android_capture.so':out/'build-x86_64/libnfsug_android_capture.so','check':out/'owned-text-check','game.gba':root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba','menu.state':root/'work/fix-menu/menu-4.state'}
run(['shell','mkdir','-p',remote]);hashes={}
try:
 for name,path in files.items():
  hashes[name]=hashlib.sha256(path.read_bytes()).hexdigest();run(['push',path,remote+'/'+name]);assert run(['shell','sha256sum',remote+'/'+name]).decode().split()[0]==hashes[name]
 run(['shell','chmod','700',remote+'/check'])
 result=run(['shell','env','LD_LIBRARY_PATH='+remote,remote+'/check',remote+'/game.gba',remote+'/menu.state'],120).decode();print(result,flush=True);assert 'PASS_ANDROID_NATIVE_MENU_TEXT snapshots=89 covered=19305' in result
 report=dict(result='PASS_ANDROID_NATIVE_MENU_TEXT',stdout=result.strip(),hashes=hashes,abi='x86_64',jni=False,gpu=False,full_frame_parity=False);(out/'owned-text-native-runtime-report.json').write_text(json.dumps(report,indent=2))
finally:
 for name in files:run(['shell','rm','-f',remote+'/'+name])
 run(['shell','rmdir',remote]);run(['emu','kill'])
