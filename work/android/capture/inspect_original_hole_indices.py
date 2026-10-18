"""Read-only comparison of original retained VRAM and unowned replay seed values at holes."""
from pathlib import Path
import struct,json,collections,hashlib
base=Path(r'C:\NFSUG-Workspace');folder=base/'NFSUG-android-source-road-sequence-local';gpu=base/'NFSUG-android-local/app-sequence-scene-gpu-tests';capture=json.loads((folder/'source-fixture-capture-report.json').read_text());audit=json.loads((gpu/'sequence-scene-gpu-android-report.json').read_text());hist=collections.Counter();initial=collections.Counter();counts=collections.Counter();rows=[]
for check in audit['coverage_details']:
 if not check['holes']:continue
 entry=capture['fixtures'][str(check['refresh'])];raw=(folder/entry['filename']).read_bytes();assert hashlib.sha256(raw).hexdigest()==entry['background_bundle_sha256'];h=struct.unpack_from('<16Q',raw);sky=raw[h[8]:h[8]+h[9]];sh=struct.unpack_from('<16Q',sky);nab=sky[sh[8]:sh[8]+sh[9]];nh=struct.unpack_from('<16Q',nab);layer=nab[nh[12]:nh[12]+nh[13]];local=collections.Counter();changes=[]
 for x,y in check['coordinates']:
  owner=int(h[5]==2 and y>=h[6]);page=entry['owners'][owner]['page'];offset=page*0xa000+y*240+x;ref=struct.unpack_from('<H',layer,20512+(y*25+offset//4096)*2)[0];index=layer[28512+ref*4096+offset%4096];bg_at=h[10+owner*2];before=raw[bg_at+80+y*240+x];mask=raw[bg_at+38480+y*240+x];assert mask==0;hist[index]+=1;initial[before]+=1;local[index]+=1;counts['same_as_unowned_replay' if index==before else 'differs_from_unowned_replay']+=1
  if index!=before:changes.append(dict(x=x,y=y,before=before,after=index))
 rows.append(dict(refresh=check['refresh'],indices=dict(local),changes=changes))
report=dict(result='ORIGINAL_HOLE_INDEX_DIAGNOSTIC',displayed_indices=dict(hist),unowned_replay_indices=dict(initial),comparison=dict(counts),checks=rows,renderer_modified=False);(gpu/'original-hole-index-report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='checks'}))
