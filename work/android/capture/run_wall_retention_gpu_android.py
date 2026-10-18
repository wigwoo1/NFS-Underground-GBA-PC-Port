from pathlib import Path
import subprocess,json,hashlib,time
base=Path(r'C:\NFSUG-Workspace');root=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');build=base/'NFSUG-android-local/app-wall-retention-gpu-tests';adb=base/'android-tools/sdk/platform-tools/adb.exe'
def run(args,timeout=45):return subprocess.run([str(adb),'-s','emulator-5556',*map(str,args)],check=True,capture_output=True,timeout=timeout).stdout
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert run(['emu','avd','name']).decode().splitlines()[0].strip()=='NFSUG_API30'
assert run(['shell','getprop','sys.boot_completed']).strip()==b'1'
manifest=json.loads((build/'apk-build-report.json').read_text());apk=build/'NFSUG-Android-Core-Preview.apk';assert digest(apk)==manifest['sha256']
restore=root/'tryout/NFSUG-Android-Core-Preview-20261015-LifecycleUpdate/NFSUG-Android-Core-Preview.apk';restore_hash='8c901a522176955ec8592a961766dead26ab7275de81a0e01a3b1de790bc383f';assert digest(restore)==restore_hash
owned=[]
try:
 run(['install','-r',apk]);print('Diagnostic installed',flush=True)
 for scope,folder,private,reportname in [('restored',base/'NFSUG-wall-retention-gpu-fixtures','restored-composition-fixtures','restored-composition-gpu-report.json'),('sequence',base/'NFSUG-android-source-road-sequence-local','sequence-scene-fixtures','retained-sequence-gpu-report.json')]:
  capture=json.loads((folder/'source-fixture-capture-report.json').read_text());names={n for e in capture['fixtures'].values() for n in (e['filename'],f"background-{e['refresh']}.rgba",f"retention-{e['refresh']}.ref")};names.update(('road-candidates.bin','original-road-events.nrj'));names.update(p.name for p in folder.glob('owner-*.nrp'))
  if scope=='restored':names.add('original-wall-history.nwh');names.update(f"wall-retention-{e['refresh']}.ref" for e in capture['fixtures'].values())
  run(['shell','run-as','org.codex.nfsugpreview','mkdir','-p','files/'+private]);hashes={}
  for name in sorted(names):
   assert Path(name).name==name;path=folder/name;sha=digest(path);tmp='/data/local/tmp/nfsug-wall-'+name;dest='files/'+private+'/'+name;owned.append(dest)
   try:run(['push',path,tmp]);run(['shell','run-as','org.codex.nfsugpreview','cp',tmp,dest])
   finally:run(['shell','rm','-f',tmp])
   assert run(['exec-out','run-as','org.codex.nfsugpreview','sha256sum',dest]).decode().split()[0]==sha;hashes[name]=sha
  print(scope+' fixtures verified '+str(len(hashes)),flush=True)
  args=['shell','am','instrument','-w','-r','-e','fixture_scope',scope,'org.codex.nfsugpreview/.RetainedSequenceGpuInstrumentation'];text=run(args,240).decode();(build/(scope+'-instrumentation.log')).write_text(text);print(text,flush=True)
  for name in [reportname,'restored-composition-gpu-failure-report.json','restored-composition-native.png','restored-composition-4k.png']:
   try:data=run(['exec-out','run-as','org.codex.nfsugpreview','cat','files/'+name]);(build/(scope+'-'+name)).write_bytes(data);owned.append('files/'+name)
   except subprocess.CalledProcessError:pass
  assert 'PASS_ANDROID_RETAINED_SEQUENCE_GPU' in text and 'INSTRUMENTATION_CODE: -1' in text
  report=json.loads((build/(scope+'-'+reportname)).read_text());assert report['coverage_holes']==0 and report['snapshots']==(9 if scope=='restored' else 49) and report['context_recreated']
  if scope=='restored':assert report['wall_source_color_checks']>206571
  report['fixtures']=hashes;report['apk_sha256']=manifest['sha256'];(build/(scope+'-verified-report.json')).write_text(json.dumps(report,indent=2));print(scope+' PASS zero holes',flush=True)
finally:
 assert run(['emu','avd','name']).decode().splitlines()[0].strip()=='NFSUG_API30'
 for dest in sorted(set(owned)):run(['shell','run-as','org.codex.nfsugpreview','rm','-f',dest])
 run(['install','-r',restore]);installed=run(['shell','pm','path','org.codex.nfsugpreview']).decode().strip().split(':',1)[1];assert run(['shell','sha256sum',installed]).decode().split()[0]==restore_hash
 print('Published APK restored and hash verified',flush=True);run(['emu','kill'])
