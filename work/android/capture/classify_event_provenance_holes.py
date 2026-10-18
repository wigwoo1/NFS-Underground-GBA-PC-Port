from pathlib import Path
import json,struct,hashlib,collections
base=Path(r'C:\NFSUG-Workspace');folder=base/'NFSUG-android-source-event-provenance-local';gpu=base/'NFSUG-android-local/app-sequence-scene-gpu-tests';capture=json.loads((folder/'source-fixture-capture-report.json').read_text());old=json.loads((base/'NFSUG-android-source-road-sequence-local/source-fixture-capture-report.json').read_text());audit=json.loads((gpu/'sequence-scene-gpu-android-report.json').read_text());owners={o['owner']['serial']:o for o in capture['road_records']};total=collections.Counter();rows=[]
for o in owners.values():
 f=o['full_replay'];assert (folder/f['filename']).read_bytes()==(base/'NFSUG-android-source-full-native-local'/f['filename']).read_bytes()
for d in audit['coverage_details']:
 if not d['holes']:continue
 entry=old['fixtures'][str(d['refresh'])];raw=(base/'NFSUG-android-source-road-sequence-local'/entry['filename']).read_bytes();h=struct.unpack_from('<16Q',raw);local=collections.Counter();cells=[]
 for x,y in d['coordinates']:
  owner=entry['owners'][int(h[5]==2 and y>=h[6])];record=owners[owner['serial']];assert record['owner']==owner;p=record['provenance'];data=(folder/p['filename']).read_bytes();assert hashlib.sha256(data).hexdigest()==p['sha256'] and p['failed']==0;at=y*240+x;kind=data[at];written=struct.unpack_from('<I',data,38400+at*4)[0];name={0:'seed_unobserved',1:'road',2:'wall',3:'model',4:'fill',5:'copy',6:'blockcopy'}[kind];age='same_interval' if owner['begin']<=written<=owner['end'] else 'earlier_interval';key=name+':'+age;total[key]+=1;local[key]+=1;cells.append(dict(x=x,y=y,kind=kind,written=written))
 rows.append(dict(refresh=d['refresh'],classification=dict(local),cells=cells))
report=dict(result='SOURCE_EVENT_HOLE_PROVENANCE',original_frames=capture['original_frames'],original_timing=capture['original_timing'],native_pages_unchanged=True,events=max(o['provenance']['events'] for o in owners.values()),total=dict(total),checks=rows,method='two disjoint sentinel replays per original source event; persistent last-observed writer kind/refresh');(gpu/'source-event-hole-report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='checks'}))
