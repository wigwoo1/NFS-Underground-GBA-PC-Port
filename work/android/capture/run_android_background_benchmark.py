from pathlib import Path
import hashlib,json,statistics,subprocess,uuid
root=Path('Y:/CODEX/NFSUG-Native-PC-Port');base=Path('C:/NFSUG-Workspace');out=base/'NFSUG-Android-Fixed-Background-Benchmark-20261017'
adb=base/'android-tools/sdk/platform-tools/adb.exe';fixture=base/'NFSUG-Android-Traffic-20261017/gap3519-results';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def run(args,timeout=45):return subprocess.run([str(adb),'-s','emulator-5556']+args,capture_output=True,check=True,timeout=timeout).stdout
owned=json.loads((out/'owned-emulator.json').read_text(encoding='utf-8-sig'));assert owned['owned'] and owned['avd']=='NFSUG_API30'
assert run(['emu','avd','name']).decode().splitlines()[0].strip()=='NFSUG_API30' and run(['shell','getprop','sys.boot_completed']).strip()==b'1'
build=json.loads((out/'build-report.json').read_text());assert sha(out/'benchmark.jar')==build['jar_sha256']
for name,digest in build['source_sha256'].items():assert sha(Path(name))==digest,name
witness=json.loads((fixture/'first-gap-report.json').read_text());names=['background.bin']+['owner0-'+kind+'.bin' for kind in ['world','road','wall','proof']]
for name in names:assert sha(fixture/name)==witness['frozen_component_sha256'][name]
def package_state():
    packages=run(['shell','pm','list','packages','org.codex.nfsugpreview']).decode().splitlines()
    if 'package:org.codex.nfsugpreview' not in packages:return dict(installed=False)
    path=run(['shell','pm','path','org.codex.nfsugpreview']).decode().strip();assert path.startswith('package:')
    return dict(installed=True,path=path,sha256=run(['shell','sha256sum',path.split(':',1)[1]]).decode().split()[0])
before=package_state();installed_before=before.get('sha256')
device='/data/local/tmp/nfsug-background-bench-'+uuid.uuid4().hex[:12]
assert device.startswith('/data/local/tmp/nfsug-background-bench-') and len(device.split('/'))==5
success=False
try:
 run(['shell','mkdir',device])
 for name in names:run(['push',str(fixture/name),device+'/'+name])
 run(['push',str(out/'benchmark.jar'),device+'/benchmark.jar'])
 (out/'run-state.json').write_text(json.dumps(dict(phase='android-fixed-scene-benchmark-live',owned_pid=owned['pid'],device_folder=device)),encoding='utf-8')
 output=run(['shell','dalvikvm','-Xmx512m','-cp',device+'/benchmark.jar','org.codex.nfsugpreview.AndroidBackgroundReuseBenchmark',device],180).decode()
 (out/'run.log').write_text(output,encoding='utf-8')
 result=json.loads(next(line for line in output.splitlines() if line.startswith('{')))
 assert result['result']=='PASS_ANDROID_FIXED_SCENE_BACKGROUND_REUSE' and result['paired_rounds']==12 and result['all_measured_scene_bytes_exact']
 assert result['background_sha256']==sha(fixture/'background.bin')
 for kind,digest in result['component_sha256'].items():assert digest==sha(fixture/('owner0-'+kind+'.bin'))
 old=result['baseline_ns'];new=result['reuse_ns'];assert len(old)==len(new)==12 and min(old+new)>0
 result.update(baseline_median_ms=statistics.median(old)/1e6,reuse_median_ms=statistics.median(new)/1e6,
               median_paired_reuse_over_baseline=statistics.median([b/a for a,b in zip(old,new)]),
               reuse_faster_pairs=sum(b<a for a,b in zip(old,new)),build_jar_sha256=build['jar_sha256'],
               runner_sha256=sha(Path(__file__)),physical_device=False,gameplay_performance_verified=False,
               limits='API30 emulator ART fixed-scene CPU wall-time component comparison, includes binding and retained preparation with warm source-owner caches. Excludes JNI acquisition, game logic, GPU, device audio, physical-phone behavior and steady-state gameplay cadence. Elapsed times include scheduling/GC; fingerprint verification occurs outside measured regions.')
 assert package_state()==before
 result['installed_preview_unchanged']=True
 result['installed_preview_present']=before['installed']
 (out/'runtime-report.json').write_text(json.dumps(result,indent=2),encoding='utf-8');success=True;print(json.dumps(result,indent=2),flush=True)
finally:
 for name in names+['benchmark.jar']:run(['shell','rm','-f',device+'/'+name])
 run(['shell','rmdir',device])
 assert run(['emu','avd','name']).decode().splitlines()[0].strip()=='NFSUG_API30';run(['emu','kill'])
 (out/'cleanup-receipt.json').write_text(json.dumps(dict(owned_emulator_stopped=True,installed_apk_sha256=installed_before,apk_installed_or_removed=False,app_files_touched=False,owned_temp_files_removed=True,benchmark_passed=success)),encoding='utf-8')
 (out/'run-state.json').write_text(json.dumps(dict(phase='terminal',passed=success)),encoding='utf-8')
