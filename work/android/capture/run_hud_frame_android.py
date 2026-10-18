from pathlib import Path
import argparse,hashlib,json,subprocess,time
p=argparse.ArgumentParser()
for n in ('adb','build','fixtures'):p.add_argument('--'+n,type=Path,required=True)
a=p.parse_args();host=json.loads((a.fixtures/'hud-frame-host-report.json').read_text());build=json.loads((a.build/'apk-build-report.json').read_text());assert host['result']=='PASS_HISTORICAL_HUD_FRAME_C_PARITY'
for name,digest in host['source_sha256'].items():assert build['source_sha256'][name.replace('\\','/')]==digest,'Stale C-parity source '+name
payloads=[]
for name,data in host['fixtures'].items():
 for extension,key in (('.nab','snapshot_sha256'),('.hud','expected_sha256')):payloads.append((name+extension,data[key]))
def run(args,timeout=40):return subprocess.run([str(a.adb),'-s','emulator-5556',*map(str,args)],capture_output=True,check=True,timeout=timeout)
for _ in range(90):
 try:
  if run(['shell','getprop','sys.boot_completed'],8).stdout.strip()==b'1':break
 except (subprocess.CalledProcessError,subprocess.TimeoutExpired):pass
 time.sleep(1)
else:raise SystemExit('Owned emulator not booted')
assert run(['emu','avd','name']).stdout.decode().splitlines()[0].strip()=='NFSUG_API30';print(run(['install','-r',a.build/'NFSUG-Android-Core-Preview.apk']).stdout.decode(),flush=True);run(['shell','run-as','org.codex.nfsugpreview','mkdir','-p','files/hud-frame-fixtures'])
for name,digest in payloads:
 path=a.fixtures/name;assert hashlib.sha256(path.read_bytes()).hexdigest()==digest;remote='/data/local/tmp/nfsug-hud-frame-'+name;private='files/hud-frame-fixtures/'+name
 try:run(['push',path,remote]);run(['shell','run-as','org.codex.nfsugpreview','cp',remote,private])
 finally:run(['shell','rm','-f',remote])
 assert run(['exec-out','run-as','org.codex.nfsugpreview','sha256sum',private]).stdout.decode().split()[0]==digest
run(['logcat','-c']);text=run(['shell','am','instrument','-w','-r','org.codex.nfsugpreview/.HudFrameInstrumentation'],180).stdout.decode();(a.build/'hud-frame-run.log').write_text(text,encoding='utf-8');print(text,flush=True);(a.build/'hud-frame-logcat.log').write_bytes(run(['logcat','-d','-s','NFSUGHudFrame:E','AndroidRuntime:E','*:S']).stdout);assert 'PASS_ANDROID_HUD_FRAME' in text and 'INSTRUMENTATION_CODE: -1' in text
report=json.loads(run(['exec-out','run-as','org.codex.nfsugpreview','cat','files/hud-frame-report.json']).stdout);assert report['verification']==host['java_stdout'];report.update(apk_sha256=build['sha256'],fixtures=host['fixtures'],scope='Complete C-verified historical HUD texture/parameter assembly on Android CPU; GPU composition/live integration pending');(a.build/'hud-frame-android-report.json').write_text(json.dumps(report,indent=2));print('Android complete historical HUD frame PASS',flush=True)
