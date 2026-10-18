"""Run C-verified UV records on only the owned Android test emulator."""
import argparse,hashlib,json,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser()
for name in ('adb','build','fixtures'):p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args();host=json.loads((a.fixtures/'road-attributes-host-report.json').read_text());build=json.loads((a.build/'apk-build-report.json').read_text());assert host['result']=='PASS_ROAD_SOURCE_ATTRIBUTE_C_PARITY' and build['instrumentation']
helper_hash=next(v for name,v in host['source_sha256'].items() if Path(name).name=='NativeRoadAttributes.java');assert build['source_sha256']['java/org/codex/nfsugpreview/NativeRoadAttributes.java']==helper_hash,'Stale compiled helper'
payloads=[('road-attribute-cases.bin','road-attributes.bin',host['fixture_cases_sha256']),('reciprocal.bin','road-reciprocal.bin',host['table_sha256'])]
for original,private,digest in payloads:assert hashlib.sha256((a.fixtures/original).read_bytes()).hexdigest()==digest
def run(args,timeout=40):return subprocess.run([str(a.adb),'-s','emulator-5556']+list(map(str,args)),capture_output=True,check=True,timeout=timeout)
for _ in range(90):
 try:
  if run(['shell','getprop','sys.boot_completed'],8).stdout.strip()==b'1':break
 except (subprocess.CalledProcessError,subprocess.TimeoutExpired):pass
 time.sleep(1)
else:raise SystemExit('Owned emulator not booted')
assert run(['emu','avd','name']).stdout.decode().splitlines()[0].strip()=='NFSUG_API30'
print(run(['install','-r',a.build/'NFSUG-Android-Core-Preview.apk']).stdout.decode(),flush=True);run(['shell','run-as','org.codex.nfsugpreview','mkdir','-p','files'])
for original,private,digest in payloads:
 remote='/data/local/tmp/nfsug-'+private
 try:run(['push',a.fixtures/original,remote]);run(['shell','run-as','org.codex.nfsugpreview','cp',remote,'files/'+private])
 finally:run(['shell','rm','-f',remote])
 assert run(['exec-out','run-as','org.codex.nfsugpreview','sha256sum','files/'+private]).stdout.decode().split()[0]==digest
run(['logcat','-c']);text=run(['shell','am','instrument','-w','-r','org.codex.nfsugpreview/.RoadAttributesInstrumentation'],120).stdout.decode();(a.build/'road-attributes-run.log').write_text(text,encoding='utf-8');print(text,flush=True)
(a.build/'road-attributes-logcat.log').write_bytes(run(['logcat','-d','-s','NFSUGRoadUV:E','AndroidRuntime:E','*:S']).stdout)
assert 'PASS_ANDROID_ROAD_SOURCE_ATTRIBUTES' in text and 'INSTRUMENTATION_CODE: -1' in text
report=json.loads(run(['exec-out','run-as','org.codex.nfsugpreview','cat','files/road-attributes-report.json']).stdout);assert report['cases']==host['cases'] and report['accepted']==host['accepted'] and report['rejected']==host['rejected'];report.update(apk_sha256=build['sha256'],host_c_reference_verified=True,fixture_cases_sha256=host['fixture_cases_sha256'],scope='CPU attribute correction only; corrected meshes/source camera/GPU integration remain unverified')
(a.build/'road-attributes-android-report.json').write_text(json.dumps(report,indent=2));print('Android source road attribute component PASS',flush=True)
