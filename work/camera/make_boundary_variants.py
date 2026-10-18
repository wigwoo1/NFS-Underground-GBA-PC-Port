"""Controlled packet variants, never used by the live renderer."""
from pathlib import Path
import struct,json,sys
p=Path('work/camera');serial=int(sys.argv[1]) if len(sys.argv)>1 else 52
def parse(b):
 sections={t:(o,n) for t,o,n in [struct.unpack_from('<3I',b,32+i*12) for i in range(5)]}
 wo,wn=sections[2];io,_=sections[5];pos=wo+8;records={}
 for i in range(struct.unpack_from('<I',b,wo+4)[0]):
  v,w,h=struct.unpack_from('<3I',b,pos);start=pos+12+v*40;end=start+w*h*4
  ident=struct.unpack_from('<5I',b,io+8+i*20)
  records.setdefault(ident,[]).append((start,end,w,h));pos=end
 assert pos==wo+wn
 return sections,records
old=bytearray((p/f'order-boundary-{serial}.bin').read_bytes());new=bytearray((p/f'order-boundary-{serial+1}.bin').read_bytes())
os,orr=parse(old);ns,nrr=parse(new)
# Both renders use exactly scene53 camera/object poses; retain source geometry/order.
o=os[1][0];n=ns[1][0];old[o+48:o+160]=new[n+48:n+160]
replaced=0;unmatched=[];changed_ranges=[]
for ident,entries in nrr.items():
 if ident not in orr:unmatched.append(list(ident));continue
 sources=orr[ident];a,z,w,h=sources[0]
 assert all(old[x:y]==old[a:z] for x,y,_,_ in sources)
 for x,y,nw,nh in entries:
  assert (w,h)==(nw,nh)
  if new[x:y]!=old[a:z]:replaced+=1;changed_ranges.append([x,y])
  new[x:y]=old[a:z]
# Verify all nontexture bytes of scene53 remain byte-identical.
original=(p/f'order-boundary-{serial+1}.bin').read_bytes();check=bytearray(new)
for x,y in changed_ranges:check[x:y]=original[x:y]
assert check==original
(p/f'boundary-fixed-pose-{serial}.bin').write_bytes(old);(p/f'boundary-fixed-material-{serial+1}.bin').write_bytes(new)
report=dict(result='PASS',texture_records_replaced=replaced,unmatched_new_identities=unmatched,old_pose=f'scene{serial+1} exact',scope='Only shared world RGBA held fixed; new surfaces and lighting/model materials not replaced. No deduplication or reorder.')
(p/f'boundary-controlled-variants-{serial}.json').write_text(json.dumps(report,indent=2));print(report)

