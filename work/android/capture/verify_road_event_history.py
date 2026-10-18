"""Verify retained road UV/address history against original gap-cell oracle."""
from pathlib import Path
import json,struct,hashlib,collections
base=Path(r'C:\NFSUG-Workspace');folder=base/'NFSUG-android-source-event-provenance-local';gpu=base/'NFSUG-android-local/app-sequence-scene-gpu-tests';capture=json.loads((folder/'source-fixture-capture-report.json').read_text());blob=(folder/'original-road-events.nrj').read_bytes();events=[];at=0;previous=0
while at<len(blob):
 h=struct.unpack_from('<12Q',blob,at);magic,version,size,epoch,ordinal,refresh,kind,count,shift,address,texture_size,stride=h;assert magic==0x314a524e and version==1 and kind==1 and stride==17 and ordinal>previous and count<=8192 and size==96+count*68+texture_size and size<=len(blob)-at
 commands=[struct.unpack_from('<17I',blob,at+96+i*68) for i in range(count)];texture=blob[at+96+count*68:at+size];events.append((h,commands,texture));at+=size;previous=ordinal
states={};state={};cursor=0
for owner in sorted(capture['road_records'],key=lambda o:o['owner']['end']):
 identity=owner['owner']
 while cursor<len(events) and events[cursor][0][5]<=identity['end']:
  h,commands,texture=events[cursor]
  for c in commands:
   assert c[0]<=15 and c[7]<=512 and c[16]<=1;u,v=c[8:10]
   for sample in range(c[7]):
    u&=c[1];v&=c[2];address=c[5]+2*((u>>16)+((v>>16)<<c[0]));offset=address-h[9];assert 0<=offset and offset+2<=len(texture)
    for duplicate in range(c[16]+1):
     for lane in range(2):
      destination=c[6]+sample*2+duplicate*240+lane;delta=destination-0x06000000;page,cell=divmod(delta,0xa000)
      if page<2 and cell<38400:state[(page,cell)]=(texture[offset+lane],h[4],h[5],offset+lane)
    u=(u+c[10])&0xffffffff;v=(v+c[11])&0xffffffff
  cursor+=1
 states[identity['serial']]=state.copy()
audit=json.loads((gpu/'sequence-scene-gpu-android-report.json').read_text());old=json.loads((base/'NFSUG-android-source-road-sequence-local/source-fixture-capture-report.json').read_text());counts=collections.Counter();retained=[]
for check in audit['coverage_details']:
 entry=old['fixtures'][str(check['refresh'])];raw=(base/'NFSUG-android-source-road-sequence-local'/entry['filename']).read_bytes();header=struct.unpack_from('<16Q',raw)
 for x,y in check['coordinates']:
  owner=entry['owners'][int(header[5]==2 and y>=header[6])];reference=next(o for o in capture['road_records'] if o['owner']==owner);page=(folder/reference['full_replay']['filename']).read_bytes();value,event,refresh,offset=states[owner['serial']][(owner['page'],y*240+x)];assert value==page[y*240+x];key='earlier_interval' if refresh<owner['begin'] else 'same_interval';counts[key]+=1;retained.append(dict(display_refresh=check['refresh'],owner_serial=owner['serial'],x=x,y=y,event=event,source_refresh=refresh,texture_offset=offset))
assert sum(counts.values())==4000
report=dict(result='PASS_ORIGINAL_ROAD_HISTORY_ADDRESSES',events=len(events),journal_bytes=len(blob),journal_sha256=hashlib.sha256(blob).hexdigest(),checked=4000,classification=dict(counts),source_address_records=retained,bitmap_rendered=False);(gpu/'road-history-address-report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='source_address_records'}))
