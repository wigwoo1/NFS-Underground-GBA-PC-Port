"""Validate/decode compact ORIGINAL wall source history against exact replay ownership."""
from pathlib import Path
import hashlib,json,struct
base=Path('C:/NFSUG-Workspace');folder=base/'NFSUG-wall-assets-fixtures'
def parse(raw):
 assert 64<=len(raw)<=64*1024*1024
 h=struct.unpack_from('<8Q',raw);assert h[0]==0x3148574e and h[1]==1 and h[2]==len(raw) and 0<h[3]<=0x7fffffffffffffff and 0<h[4]<=1024 and 0<h[5]<=65536 and h[6:]==(0,0)
 assets={};events=[];at=64;previous=0;frame=0
 while at<len(raw):
  tag,size=struct.unpack_from('<2Q',raw,at);assert size>=64 and size<=len(raw)-at
  if tag==1:
   a=struct.unpack_from('<8Q',raw,at);assert a[2]==len(assets)+1 and a[3] in (1,2) and a[5]==(65536 if a[3]==1 else 4081) and size==64+a[5] and a[6:]==(0,0)
   assert 0x02000000<=a[4]<=0x0a000000-a[5] and (a[3]!=1 or a[4]>=0x08000000)
   assets[a[2]]=(a[3],a[4],raw[at+64:at+size])
  else:
   assert tag==2 and size==176;e=struct.unpack_from('<12Q',raw,at);c=struct.unpack_from('<20I',raw,at+96)
   assert e[2]>previous and frame<=e[3]<=0xffffffff and e[7]==1 and e[8] in (0,1) and e[9:]==(0,0,0) and e[4] in assets
   assert assets[e[4]][0]==1 and assets[e[4]][1]==e[6]==c[9] and c[19]<=320 and c[3]<=10 and 1<=c[4]<=1024
   if e[8]:
    assert e[5] in assets and assets[e[5]][0]==2;offset=struct.unpack_from('<h',struct.pack('<20I',*c),42)[0];assert assets[e[5]][1]==(c[5]+offset)&0xffffffff
   else:assert e[5]==0
   events.append((e,c));previous=e[2];frame=e[3]
  at+=size
 assert at==len(raw) and len(assets)==h[4] and len(events)==h[5];return h,assets,events
raw=(folder/'original-wall-history.nwh').read_bytes();header,assets,events=parse(raw);capture=json.loads((folder/'source-fixture-capture-report.json').read_text());state={};cursor=0;checks=0;source_samples=0
for record in sorted(capture['road_records'],key=lambda r:r['owner']['end']):
 owner=record['owner']
 while cursor<len(events) and events[cursor][0][3]<=owner['end']:
  e,c=events[cursor];shift=c[3];uvshift=15;texture=c[9];step=c[11]
  if c[6] and step>0x1b000:assert shift>=2;shift-=2;uvshift=17;texture=(texture+c[7])&0xffffffff
  texture=((texture+((c[13]&c[16])>>uvshift))&0xffffffff)&~1;dest=(c[17]+((c[2]*(c[1]>>14))<<1))&0xffffffff;vertical=c[18];mask=((c[4]<<15)-1)&0xffffffff;data=assets[e[4]][2]
  for row in range(c[19]):
   vertical&=mask;address=(texture+((vertical>>uvshift)<<shift))&0xffffffff;offset=address-e[6];assert 0<=offset<len(data);value=data[offset];source_samples+=1
   if value:
    asset=e[4]
    if e[8]:offset=value*16;asset=e[5];value=assets[asset][2][offset]
    for lane in range(2):
     page,cell=divmod((dest&~1)+lane-0x06000000,0xa000)
     if page in (0,1) and cell<38400:state[(page,cell)]=(value,e[3],asset,offset,e[2])
   dest=(dest+(c[2]<<1))&0xffffffff;vertical=(vertical+step)&0xffffffff
  cursor+=1
 proof=(folder/record['provenance']['filename']).read_bytes();original=(folder/record['full_replay']['filename']).read_bytes();assert len(proof)==192000 and len(original)==38400
 for cell in range(38400):
  if proof[cell]!=2:continue
  sample=state.get((owner['page'],cell));assert sample and sample[0]==original[cell] and sample[1]==struct.unpack_from('<I',proof,38400+cell*4)[0],(owner['serial'],cell,sample);checks+=1
rejected=0
for at in (0,8,16,24,32,40,48,56,64,72,80,88,104):
 bad=bytearray(raw);struct.pack_into('<Q',bad,at,0xffffffffffffffff)
 try:parse(bad)
 except (AssertionError,struct.error,KeyError,ValueError):rejected+=1
 else:raise AssertionError(('Malformed accepted',at))
assert checks>200000 and rejected==13
report=dict(result='PASS_COMPACT_ORIGINAL_WALL_HISTORY',bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),assets=len(assets),texture_assets=sum(a[0]==1 for a in assets.values()),shade_assets=sum(a[0]==2 for a in assets.values()),events=len(events),shaded_events=sum(e[0][8] for e in events),decoded_source_samples=source_samples,owner_wall_index_and_writer_checks=checks,malformed_rejected=rejected,finished_pixels_stored=False,gpu_rendering_tested=False)
(folder/'compact-wall-history-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
