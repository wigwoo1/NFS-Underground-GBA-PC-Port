from pathlib import Path
import struct,json
p=Path(__file__).resolve().parent
def read(kind):
 raw=(p/f'object-replay-143-{kind}-queue.bin').read_bytes();rows=[]
 for i in range(struct.unpack_from('<I',raw)[0]):
  offset=4+i*2068;record=struct.unpack_from('<8H',raw,offset+4)
  rows.append(dict(index=i,region=record[0],bounds=record[1:5],flags=record[5],depth=record[6],draws=struct.unpack_from('<I',raw,offset)[0]))
 return rows
old,new=read('captured'),read('sampled')
regions={row['region'] for row in old}
new_regions=[row for row in new if row['region'] not in regions]
assert [row['region'] for row in new_regions]==[18,16]
assert sum(row['draws'] for row in new_regions)==3
report=dict(result='PASS',captured_regions=len(old),sampled_regions=len(new),new_regions=new_regions,scope='Queue topology diagnostic: three of four wall entrants belong to newly visible regions; road/object emission and ordering for those regions are not covered by wall-only insertion.')
(p/'object-queue-topology-tests.json').write_text(json.dumps(report,indent=2));print(report)
