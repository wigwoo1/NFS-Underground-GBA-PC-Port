from pathlib import Path
import struct,json
from owned_partition_bounds import record
from owned_portal_transform import transform,project_edge
p=Path('work/camera');source=(p/'owned-projected-portals.bin').read_bytes();recip=(p/'road-correction-reciprocal.bin').read_bytes();table=struct.unpack('<'+str(len(recip)//4)+'I',recip)
portals={}
for o in range(0,len(source),368):
 refresh,state,point=struct.unpack_from('<3I',source,o+4);m=struct.unpack_from('<12i',source,o+168);fb=source[o+216:o+280];flip=struct.unpack_from('<i',source,o+364)[0]
 a=transform(*struct.unpack_from('<2i',source,o+32),m);b=transform(*struct.unpack_from('<2i',source,o+100),m)
 result=project_edge(a,b,struct.unpack_from('<i',fb,16)[0],struct.unpack_from('<I',fb,28)[0],struct.unpack_from('<h',fb,8)[0],table,bool(flip))
 portals.setdefault((refresh,point),set()).add(result)
consumers=json.loads((p/'owned-clip-writers-runtime.json').read_text())['records'];roots={}
for r in consumers:
 if r['source']=='0x20086bc':roots[r['refresh']]=tuple(r['source_halfwords'][:7])
raw=(p/'owned-partitions.bin').read_bytes();state={};checks=[]
for o in range(0,len(raw),96):
 v=struct.unpack_from('<20I8H',raw,o);refresh,point,parent_address,out_address=v[1],v[3],v[17],v[18]
 if refresh not in state:state[refresh]={0x020086bc:roots[refresh]}
 parent=state[refresh][parent_address]
 assert parent[1:3]==(v[7],v[8]) and parent[5:7]==(v[9],v[10])
 candidates=portals[(refresh,point)];assert len(candidates)==1,candidates
 left,right,near,z,nz=next(iter(candidates))
 result=record(v[13],left,right,near,parent,v[11],v[12],v[14],z,nz)
 assert result==tuple(v[20:27]),(result,v[20:27])
 state[refresh][out_address]=result;checks.append(dict(refresh=refresh,parent=hex(parent_address),output=hex(out_address),depth=result[6]))
assert len(checks)==37
r=dict(result='PASS_RAW_PORTAL_PARTITION_HIERARCHY',records=len(checks),scenes=len(state),max_depth=max(x['depth'] for x in checks),checks=checks,scope='Raw world endpoint projection plus reconstructed parent outputs for accepted records; root and traversal/selection still supplied from original capture.')
(p/'owned-partition-hierarchy-tests.json').write_text(json.dumps(r,indent=2));print(r['result'],r['records'],r['scenes'],r['max_depth'])
