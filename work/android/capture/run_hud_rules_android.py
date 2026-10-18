from pathlib import Path
import argparse,hashlib,json,subprocess,time
p=argparse.ArgumentParser()
for n in ('adb','build','rules','candidates'):p.add_argument('--'+n,type=Path,required=True)
a=p.parse_args();build=json.loads((a.build/'apk-build-report.json').read_text());rules=json.loads((a.rules/'hud-rules-host-report.json').read_text());candidates=json.loads((a.candidates/'hud-candidates-host-report.json').read_text());assert rules['result']=='PASS_HUD_RULES_C_PARITY' and candidates['result']=='PASS_HUD_CANDIDATES_C_PARITY'
for report in (rules,candidates):
 for name,digest in report['source_sha256'].items():assert build['source_sha256'][name.replace('\\','/')]==digest,'Stale verified source '+name
payloads=[(a.rules/'hud-rules-cases.bin','hud-rules.bin',rules['fixture_sha256']),(a.candidates/'hud-candidates-cases.bin','hud-candidates.bin',candidates['fixture_sha256'])]
for path,private,digest in payloads:assert hashlib.sha256(path.read_bytes()).hexdigest()==digest
def run(args,timeout=40):return subprocess.run([str(a.adb),'-s','emulator-5556',*map(str,args)],capture_output=True,check=True,timeout=timeout)
for _ in range(90):
 try:
  if run(['shell','getprop','sys.boot_completed'],8).stdout.strip()==b'1':break
 except (subprocess.CalledProcessError,subprocess.TimeoutExpired):pass
 time.sleep(1)
else:raise SystemExit('Owned emulator not booted')
assert run(['emu','avd','name']).stdout.decode().splitlines()[0].strip()=='NFSUG_API30';print(run(['install','-r',a.build/'NFSUG-Android-Core-Preview.apk']).stdout.decode(),flush=True);run(['shell','run-as','org.codex.nfsugpreview','mkdir','-p','files'])
for path,private,digest in payloads:
 remote='/data/local/tmp/nfsug-'+private
 try:run(['push',path,remote]);run(['shell','run-as','org.codex.nfsugpreview','cp',remote,'files/'+private])
 finally:run(['shell','rm','-f',remote])
 assert run(['exec-out','run-as','org.codex.nfsugpreview','sha256sum','files/'+private]).stdout.decode().split()[0]==digest
run(['logcat','-c']);text=run(['shell','am','instrument','-w','-r','org.codex.nfsugpreview/.HudRulesInstrumentation'],180).stdout.decode();(a.build/'hud-rules-run.log').write_text(text,encoding='utf-8');print(text,flush=True);(a.build/'hud-rules-logcat.log').write_bytes(run(['logcat','-d','-s','NFSUGHudRules:E','AndroidRuntime:E','*:S']).stdout);assert 'PASS_ANDROID_HUD_RULES_CANDIDATES' in text and 'INSTRUMENTATION_CODE: -1' in text
report=json.loads(run(['exec-out','run-as','org.codex.nfsugpreview','cat','files/hud-rules-report.json']).stdout);assert report['rules_verification']==rules['java_stdout'] and report['candidates_verification']==candidates['java_stdout'];report.update(apk_sha256=build['sha256'],rules_fixture_sha256=rules['fixture_sha256'],candidates_fixture_sha256=candidates['fixture_sha256'],scope='C-verified HUD window/blend evaluator and candidates on Android CPU; native scene GPU composition remains pending');(a.build/'hud-rules-android-report.json').write_text(json.dumps(report,indent=2));print('Android HUD rules/candidates PASS',flush=True)
