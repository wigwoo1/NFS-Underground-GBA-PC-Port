from pathlib import Path
import struct,json
from owned_partition_bounds import bounds
p=Path('work/camera');raw=(p/'owned-partitions.bin').read_bytes();assert len(raw)%96==0;checks=[]
for offset in range(0,len(raw),96):
 v=struct.unpack_from('<20I8H',raw,offset);assert v[0]==0x3150434e
 signed=lambda x:x if x<0x80000000 else x-0x100000000
 left,right=bounds(signed(v[4]),signed(v[5]),v[6],v[7],v[8])
 flags=v[9]&128
 if v[14]&0x800:flags=128
 if min(signed(v[15]),signed(v[16]))>0x800:flags|=1
 expected=(v[13]&65535,left&65535,right&65535,v[11],v[12],flags,(v[10]+1)&65535)
 assert tuple(v[20:27])==expected,(v,expected)
 checks.append(dict(refresh=v[1],left=left,right=right,near_flags=v[6]))
assert checks
r=dict(result='PASS_RECOVERED_PARTITION_RECORDS',records=len(checks),checks=checks,scope='Exact bounds/descriptor/flags/depth fields for captured accepted partition records; upstream camera projection and visibility selection remain original.')
(p/'owned-partition-tests.json').write_text(json.dumps(r,indent=2));print(r['result'],len(checks))
