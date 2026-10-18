from pathlib import Path
import argparse
parser=argparse.ArgumentParser();parser.add_argument("--folder",type=Path,default=Path(r'C:\NFSUG-Workspace\NFSUG-android-source-road-sequence-local'));args=parser.parse_args()
import json,struct,hashlib,subprocess
root=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');folder=args.folder;capture=json.loads((folder/'source-fixture-capture-report.json').read_text());parts=[]
for record in capture['road_records']:
 owner=record['owner']
 for command in record['commands']:
  if command['kind']!=1:continue
  if not command.get('asset_available',False):
   proof=command['diagnostic'];assert proof[0]==6 and proof[4]==1 and proof[5]==0
   parts.append(struct.pack('<Q10I',owner['epoch'],owner['serial'],owner['begin'],owner['end'],owner['page'],*command['identity'],0)+struct.pack('<16I',*proof));continue
  name=f"road-{owner['serial']}-{command['passno']}-{command['ordinal']}.nfre";asset=next(a for a in record['assets'] if a['filename']==name);raw=(folder/name).read_bytes();assert hashlib.sha256(raw).hexdigest()==asset['sha256'];parts.append(struct.pack('<Q10I',owner['epoch'],owner['serial'],owner['begin'],owner['end'],owner['page'],*command['identity'],len(raw))+raw)
(folder/'road-candidates.bin').write_bytes(struct.pack('<I',len(parts))+b''.join(parts));java=root/'work/android/java';test=root/'work/android/tests/org/codex/nfsugpreview/RoadSequenceBindingTest.java';helper=root/'work/android/tests/org/codex/nfsugpreview/RoadBindingsTest.java';classes=folder/'binding-classes';classes.mkdir(exist_ok=True);jdk=Path(r'C:\NFSUG-Workspace\android-tools\jdk-21.0.12.1+1');subprocess.run([str(jdk/'bin/javac.exe'),'--release','8','-sourcepath',str(java),'-d',str(classes),str(test),str(helper)],check=True);r=subprocess.run([str(jdk/'bin/java.exe'),'-cp',str(classes),'org.codex.nfsugpreview.RoadSequenceBindingTest',str(folder)],check=True,capture_output=True,text=True);print(r.stdout);(folder/'road-sequence-binding-report.json').write_text(json.dumps(dict(result=r.stdout.strip(),candidates=len(parts),gpu=False),indent=2))
