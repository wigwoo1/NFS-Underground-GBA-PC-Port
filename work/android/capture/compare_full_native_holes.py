from pathlib import Path
import json,struct,collections,hashlib
base=Path(r'C:\NFSUG-Workspace');old=base/'NFSUG-android-source-road-sequence-local';folder=base/'NFSUG-android-source-full-native-local';gpu=base/'NFSUG-android-local/app-sequence-scene-gpu-tests';capture=json.loads((folder/'source-fixture-capture-report.json').read_text());original=json.loads((old/'source-fixture-capture-report.json').read_text());audit=json.loads((gpu/'sequence-scene-gpu-android-report.json').read_text());pages={}
for owner in capture['road_records']:
 f=owner['full_replay'];data=(folder/f['filename']).read_bytes();assert len(data)==38400 and hashlib.sha256(data).hexdigest()==f['sha256'];pages[owner['owner']['serial']]=(owner['owner'],data)
counts=collections.Counter();rows=[]
for check in audit['coverage_details']:
 if not check['holes']:continue
 entry=original['fixtures'][str(check['refresh'])];raw=(old/entry['filename']).read_bytes();h=struct.unpack_from('<16Q',raw);sky=raw[h[8]:h[8]+h[9]];sh=struct.unpack_from('<16Q',sky);nab=sky[sh[8]:sh[8]+sh[9]];nh=struct.unpack_from('<16Q',nab);layer=nab[nh[12]:nh[12]+nh[13]];local=collections.Counter();mismatch=[]
 for x,y in check['coordinates']:
  index=int(h[5]==2 and y>=h[6]);owner=entry['owners'][index];identity,page=pages[owner['serial']];assert owner==identity;offset=owner['page']*0xa000+y*240+x;ref=struct.unpack_from('<H',layer,20512+(y*25+offset//4096)*2)[0];expected=layer[28512+ref*4096+offset%4096];actual=page[y*240+x];key='native_source_exact' if actual==expected else 'native_source_mismatch';counts[key]+=1;local[key]+=1
  if actual!=expected:mismatch.append(dict(x=x,y=y,expected=expected,actual=actual))
 rows.append(dict(refresh=check['refresh'],counts=dict(local),mismatches=mismatch))
report=dict(result='FULL_NATIVE_SOURCE_HOLE_COMPARISON',original_frames=capture['original_frames'],original_timing=capture['original_timing'],counts=dict(counts),checks=rows,renderer_modified=False);(gpu/'full-native-hole-report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='checks'}))
