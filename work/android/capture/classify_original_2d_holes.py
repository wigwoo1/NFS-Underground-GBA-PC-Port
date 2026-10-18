from pathlib import Path
import json,struct,collections,hashlib
base=Path(r'C:\NFSUG-Workspace');folder=base/'NFSUG-android-source-all-2d-local';r=json.loads((folder/'source-fixture-capture-report.json').read_text());gpu=base/'NFSUG-android-local/app-sequence-scene-gpu-tests';holes=json.loads((gpu/'sequence-scene-gpu-android-report.json').read_text());maps={};operations=[]
for owner in r['road_records']:
 mapping={}
 for op in owner['operations_2d']:
  raw=(folder/op['filename']).read_bytes();assert hashlib.sha256(raw).hexdigest()==op['sha256'];h=struct.unpack_from('<10I',raw);assert h[0] in (0x4943464e,0x4643464e) and len(raw)==40+h[9]
  operations.append(dict(serial=owner['owner']['serial'],kind=op['meta'][2],page=h[3],offset=h[4],bytes=h[9],refresh=op['meta'][3],caller=hex(op['meta'][4])))
  for at in range(h[4],h[4]+h[9]):mapping[(h[3],at%240,at//240)]=op['meta'][2]
 maps[owner['owner']['serial']]=mapping
counts=collections.Counter();rows=[]
for check in holes['coverage_details']:
 entry=r['fixtures'][str(check['refresh'])];old=base/'NFSUG-android-source-road-sequence-local'/entry['filename'];assert hashlib.sha256(old.read_bytes()).hexdigest()==entry['background_bundle_sha256'];h=struct.unpack_from('<16Q',(folder/entry['filename']).read_bytes());c=collections.Counter()
 for x,y in check['coordinates']:
  index=int(h[5]==2 and y>=h[6]);owner=entry['owners'][index];kind=maps[owner['serial']].get((owner['page'],x,y),0);c['fill' if kind==2 else 'copy' if kind==1 else 'not_2d']+=1
 counts.update(c)
 if check['holes']:rows.append(dict(refresh=check['refresh'],counts=dict(c)))
report=dict(result='ORIGINAL_2D_HOLE_CLASSIFICATION',original_frames=r['original_frames'],original_timing=r['original_timing'],snapshots=len(r['fixtures']),operations=operations,total=dict(counts),checks=rows);(gpu/'original-2d-hole-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(result=report['result'],operations=len(operations),total=report['total'],kinds=dict(collections.Counter(o['kind'] for o in operations)))))
