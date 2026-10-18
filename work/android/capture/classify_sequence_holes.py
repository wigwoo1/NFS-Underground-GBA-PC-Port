"""Classify measured holes against source span addresses, never projected matching."""
from pathlib import Path
import json,struct,collections,hashlib
base=Path(r'C:\NFSUG-Workspace');folder=base/'NFSUG-android-source-road-sequence-local';gpu=base/'NFSUG-android-local/app-sequence-scene-gpu-tests';capture=json.loads((folder/'source-fixture-capture-report.json').read_text());report=json.loads((gpu/'sequence-scene-gpu-android-report.json').read_text());footprints={}
for owner in capture['road_records']:
 assets={a['filename']:a for a in owner['assets']};by_identity={}
 for command in owner['commands']:
  if command['kind']!=1 or not command.get('asset_available'):continue
  name=f"road-{owner['owner']['serial']}-{command['passno']}-{command['ordinal']}.nfre";raw=(folder/name).read_bytes();assert hashlib.sha256(raw).hexdigest()==assets[name]['sha256'];identity=tuple(command['identity']);normalized=raw[:12]+bytes(4)+raw[16:]
  if identity in by_identity:assert by_identity[identity][0]==normalized;continue
  h=struct.unpack_from('<10I',raw);cells=set()
  for i in range(h[5]):
   s=struct.unpack_from('<20I',raw,40+i*80);page=0x0600a000 if s[0]>=0x0600a000 else 0x06000000
   for duplicate in range(s[3]+1):
    for lane in range(s[1]*2):
     at=s[0]-page+duplicate*240+lane
     if 0<=at<38400:cells.add((at%240,at//240))
  by_identity[identity]=(normalized,cells)
 footprints[owner['owner']['serial']]=by_identity
summary=[];total=collections.Counter()
for d in report['coverage_details']:
 if not d['holes']:continue
 entry=capture['fixtures'][str(d['refresh'])];raw=(folder/entry['filename']).read_bytes();assert hashlib.sha256(raw).hexdigest()==entry['background_bundle_sha256'];h=struct.unpack_from('<16Q',raw);sky=raw[h[8]:h[8]+h[9]];sh=struct.unpack_from('<16Q',sky);nab=sky[sh[8]:sh[8]+sh[9]];nh=struct.unpack_from('<16Q',nab);owners=[]
 for owner in range(nh[7]):
  packet=nab[nh[8+owner*2]:nh[8+owner*2]+nh[9+owner*2]];serial=struct.unpack_from('<I',packet,16)[0];wo=struct.unpack_from('<I',packet,48)[0];worlds=struct.unpack_from('<I',packet,wo+4)[0];io,isz=struct.unpack_from('<II',packet,84);ident=packet[io:io+isz];entries=struct.unpack_from('<I',ident,4)[0];bound_at=8+entries*20;assert ident[bound_at:bound_at+4]==b'NFB2';roads=[]
  for i in range(worlds):
   identity=struct.unpack_from('<5I',ident,8+i*20)
   if identity[0]!=1:continue
   bounds=struct.unpack_from('<4H',ident,bound_at+16+i*8);source=footprints[serial].get(identity);roads.append((bounds,set() if source is None else source[1]))
  owners.append(roads)
 counts=collections.Counter();unmatched=[]
 for x,y in d['coordinates']:
  owner=int(h[5]==2 and y>=h[6]);matches=[bounds for bounds,cells in owners[owner] if (x,y) in cells]
  if not matches:counts['not_written_by_road']+=1;unmatched.append([x,y]);continue
  reasons=set()
  for left,right,top,bottom in matches:
   if x<left:reasons.add('left_of_bounds')
   if x>=right:reasons.add('right_of_bounds')
   if y<top:reasons.add('above_bounds')
   if y>=bottom:reasons.add('below_bounds')
   if left<=x<right and top<=y<bottom:reasons.add('inside_bounds')
  for reason in reasons:counts[reason]+=1
  counts['written_by_road']+=1
 total.update(counts);summary.append(dict(refresh=d['refresh'],kind=d['kind'],holes=d['holes'],classification=dict(counts),unmatched=unmatched))
result=dict(result='SOURCE_SPAN_HOLE_CLASSIFICATION',total=dict(total),checks=summary,source='original NFRE destination/count/row-duplication, exact identity and owner rows');(gpu/'source-span-hole-report.json').write_text(json.dumps(result,indent=2));print(json.dumps(dict(result=result['result'],total=result['total'],affected_checks=len(summary))))
