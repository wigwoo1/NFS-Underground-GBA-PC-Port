from pathlib import Path
import argparse
parser=argparse.ArgumentParser();parser.add_argument("--folder",type=Path,default=Path(r'C:\NFSUG-Workspace\NFSUG-wall-assets-fixtures'));args=parser.parse_args()
import struct,json,hashlib,subprocess
root=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');folder=args.folder;capture=json.loads((folder/'source-fixture-capture-report.json').read_text());owners={r['owner']['serial']:r for r in capture['road_records']};proofs={};pages={}
for serial,record in owners.items():
 owner=record['owner'];p=record['provenance'];raw=(folder/p['filename']).read_bytes();assert len(raw)==192000 and hashlib.sha256(raw).hexdigest()==p['sha256'];header=(0x3150524e,1,192080,owner['epoch'],serial,owner['begin'],owner['end'],owner['end']+1,owner['page'],38400);(folder/f'owner-{serial}.nrp').write_bytes(struct.pack('<10Q',*header)+raw);proofs[serial]=raw;f=record['full_replay'];pages[serial]=(folder/f['filename']).read_bytes();assert hashlib.sha256(pages[serial]).hexdigest()==f['sha256']
for entry in capture['fixtures'].values():
 raw=(folder/entry['filename']).read_bytes();h=struct.unpack_from('<16Q',raw);records=[]
 for cell in range(38400):
  y=cell//240;owner=entry['owners'][int(h[5]==2 and y>=h[6])];serial=owner['serial']
  if proofs[serial][cell]==2:records.append((cell,pages[serial][cell]))
 (folder/f"wall-retention-{entry['refresh']}.ref").write_bytes(struct.pack('<I',len(records))+b''.join(struct.pack('<2I',*r) for r in records))
classes=folder/'wall-retention-classes';classes.mkdir(exist_ok=True);jdk=Path(r'C:\NFSUG-Workspace\android-tools\jdk-21.0.12.1+1');java=root/'work/android/java';test=root/'work/android/tests/org/codex/nfsugpreview/WallRetentionTest.java';subprocess.run([str(jdk/'bin/javac.exe'),'--release','8','-sourcepath',str(java),'-d',str(classes),str(test)],check=True);r=subprocess.run([str(jdk/'bin/java.exe'),'-cp',str(classes),'org.codex.nfsugpreview.WallRetentionTest',str(folder)],check=True,capture_output=True,text=True);print(r.stdout);(folder/'wall-retention-host-report.json').write_text(json.dumps(dict(result=r.stdout.strip(),gpu=False,android_runtime=False,source_hashes={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [java/'org/codex/nfsugpreview/NativeWallHistory.java',java/'org/codex/nfsugpreview/NativeWallRetention.java',test,Path(__file__)]},selection='all original last-writer wall cells, not GPU holes'),indent=2))
