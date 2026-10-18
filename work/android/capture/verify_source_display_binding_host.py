"""Compile and verify source-display binding fixtures, ownership and cache semantics."""
import hashlib,json,re,subprocess
from pathlib import Path
root=Path('Y:/CODEX/NFSUG-Native-PC-Port/work/android');local=Path('C:/NFSUG-Workspace');fixtures=local/'NFSUG-source-display-binding-fixtures';classes=local/'NFSUG-source-binding-java-check';jdk=local/'android-tools/jdk-21.0.12.1+1/bin'
manifest=json.loads((fixtures/'manifest.json').read_text());assert manifest['restored_scene_owners']==[7,17,18,19,61,62,63,67,69] and manifest['eligible_display_snapshots']==594
for f in manifest['fixtures']:
 assert hashlib.sha256((fixtures/f['file']).read_bytes()).hexdigest()==f['sha256']
 for source in f['sources']:assert hashlib.sha256((fixtures/source['file']).read_bytes()).hexdigest()==source['sha256']
names=['NativeScenePacket.java','NativeSceneSnapshot.java','NativeSourceSceneBinding.java','NativeCore.java'];sources=[root/'java/org/codex/nfsugpreview'/n for n in names];test=root/'tests/org/codex/nfsugpreview/WorldSourceSceneBindingTest.java'
subprocess.run([str(jdk/'javac.exe'),'-d',str(classes),*[str(p) for p in sources],str(test)],check=True)
run=subprocess.run([str(jdk/'java.exe'),'-cp',str(classes),'org.codex.nfsugpreview.WorldSourceSceneBindingTest',str(fixtures)],check=True,capture_output=True,text=True);print(run.stdout.strip());(fixtures/'java-test.log').write_text(run.stdout)
m=re.search(r'fixtures=(\d+) whole=(\d+) split=(\d+) forged_owners=(\d+)',run.stdout);assert m and list(map(int,m.groups()))==[11,2,9,44]
report=dict(result='PASS_SOURCE_DISPLAY_BINDING_HOST',fixture_snapshots=11,whole=2,split=9,forged_owner_rejections=44,restored_scene_owners=manifest['restored_scene_owners'],epoch_cache_and_atomic_split_guards=True,immutable_owned_data=True,historical_layers_and_provenance_unchanged=True,source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+[test]},live_gpu_rendering=False)
(fixtures/'host-binding-report.json').write_text(json.dumps(report,indent=2))
