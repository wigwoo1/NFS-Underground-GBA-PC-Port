from pathlib import Path
import json,struct,hashlib,subprocess
root=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');folder=Path(r'C:\NFSUG-Workspace\NFSUG-android-source-road-assets-local');capture=json.loads((folder/'source-fixture-capture-report.json').read_text());parts=[]
for record in capture['road_records']:
 owner=record['owner']
 for command in record['commands']:
  if command['kind']!=1:continue
  name=f"road-{owner['serial']}-{command['passno']}-{command['ordinal']}.nfre";asset=next(a for a in record['assets'] if a['filename']==name);raw=(folder/name).read_bytes();assert hashlib.sha256(raw).hexdigest()==asset['sha256'];parts.append(struct.pack('<Q10I',owner['epoch'],owner['serial'],owner['begin'],owner['end'],owner['page'],*command['identity'],len(raw))+raw)
(folder/'road-candidates.bin').write_bytes(struct.pack('<I',len(parts))+b''.join(parts));java=root/'work/android/java';test=root/'work/android/tests/org/codex/nfsugpreview/RoadBindingsTest.java';classes=folder/'binding-classes';classes.mkdir(exist_ok=True);jdk=Path(r'C:\NFSUG-Workspace\android-tools\jdk-21.0.12.1+1');subprocess.run([str(jdk/'bin/javac.exe'),'--release','8','-sourcepath',str(java),'-d',str(classes),str(test)],check=True);r=subprocess.run([str(jdk/'bin/java.exe'),'-cp',str(classes),'org.codex.nfsugpreview.RoadBindingsTest',str(folder)],check=True,capture_output=True,text=True);print(r.stdout);(folder/'road-binding-host-report.json').write_text(json.dumps(dict(result=r.stdout.strip(),candidates=len(parts),gpu=False),indent=2))
