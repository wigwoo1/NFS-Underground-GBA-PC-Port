"""Run wall JNI checks only on owned API30 emulator, then restore published app."""
from pathlib import Path
import subprocess,json,hashlib,time,argparse
parser=argparse.ArgumentParser();parser.add_argument('--app',type=Path);args=parser.parse_args()
b=Path(r'C:\NFSUG-Workspace');r=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');build=args.app or b/'NFSUG-android-local/app-complete-scene-gpu-tests';fixtures=b/'NFSUG-complete-scene-gpu-fixtures';adb=b/'android-tools/sdk/platform-tools/adb.exe'
def run(args,timeout=45):return subprocess.run([str(adb),'-s','emulator-5556',*map(str,args)],check=True,capture_output=True,timeout=timeout).stdout
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for i in range(60):
 try:
  if run(['shell','getprop','sys.boot_completed'],5).strip()==b'1':break
 except (subprocess.CalledProcessError,subprocess.TimeoutExpired):pass
 time.sleep(1)
else:raise RuntimeError('Owned test emulator did not boot')
assert run(['emu','avd','name']).decode().splitlines()[0].strip()=='NFSUG_API30'
restore=r/'tryout/NFSUG-Android-Core-Preview-20261015-LifecycleUpdate/NFSUG-Android-Core-Preview.apk';restore_sha='8c901a522176955ec8592a961766dead26ab7275de81a0e01a3b1de790bc383f';assert sha(restore)==restore_sha
manifest=json.loads((fixtures/'manifest.json').read_text());apk=json.loads((build/'apk-build-report.json').read_text());assert sha(Path(apk['apk']))==apk['sha256'];owned=[]
try:
 run(['install','-r',apk['apk']]);print('Diagnostic installed',flush=True)
 for name,digest in manifest.items():
  assert Path(name).name==name and sha(fixtures/name)==digest;temp='/data/local/tmp/nfsug-'+name;dest='files/'+name;owned.append(dest)
  try:run(['push',fixtures/name,temp]);run(['shell','run-as','org.codex.nfsugpreview','cp',temp,dest])
  finally:run(['shell','rm','-f',temp])
  assert run(['exec-out','run-as','org.codex.nfsugpreview','sha256sum',dest]).decode().split()[0]==digest
 print(str(len(manifest))+' named private fixtures hash verified',flush=True)
 run(['logcat','-c']);text=run(['shell','am','instrument','-w','-r','org.codex.nfsugpreview/.CompleteSceneGpuInstrumentation'],240).decode();(build/'complete-scene-gpu-instrumentation.log').write_text(text);print(text,flush=True);(build/'complete-scene-logcat.txt').write_bytes(run(['logcat','-d','-v','threadtime']))
 for name in ('complete-scene-native.png','complete-scene-4k.png','complete-scene-gpu-failure.json'):
  try:run(['shell','run-as','org.codex.nfsugpreview','test','-f','files/'+name]);(build/name).write_bytes(run(['exec-out','run-as','org.codex.nfsugpreview','cat','files/'+name]));owned.append('files/'+name)
  except subprocess.CalledProcessError:pass
 assert 'PASS_ANDROID_COMPLETE_RETAINED_GPU' in text and 'INSTRUMENTATION_CODE: -1' in text
 raw=run(['exec-out','run-as','org.codex.nfsugpreview','cat','files/complete-scene-gpu-report.json']);owned.append('files/complete-scene-gpu-report.json');report=json.loads(raw);assert report['native_gpu_frames']==9 and report['four_k_frames']==3 and report['coverage_holes']==0 and report['context_recreated'] and report['render_thread_handoff_after_core_close'] and report['pc_identical_source_backgrounds']==9 and report['unowned_warmup_rejected']==2 and report['retained_display_checks']==9 and report['retained_road_cells']==100870 and report['retained_wall_cells']==206571 and report['pc_identical_road_owners']==13 and report['pc_identical_proof_owners']==13 and report['wall_owners']==148 and report['pc_identical_wall_owners']==13 and report['older_owner_immutable_checks']==147 and report['source_display_snapshots']==594
 report['apk_sha256']=apk['sha256'];report['fixtures']=manifest;(build/'complete-scene-gpu-android-report.json').write_text(json.dumps(report,indent=2))
finally:
 assert run(['emu','avd','name']).decode().splitlines()[0].strip()=='NFSUG_API30'
 for dest in owned:run(['shell','run-as','org.codex.nfsugpreview','rm','-f',dest])
 run(['install','-r',restore]);path=run(['shell','pm','path','org.codex.nfsugpreview']).decode().strip().split(':',1)[1];assert run(['shell','sha256sum',path]).decode().split()[0]==restore_sha;print('Published APK restored and installed hash verified',flush=True);run(['emu','kill'])


