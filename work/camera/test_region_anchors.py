from pathlib import Path
import json,struct
from region_anchors import root_anchors
p=Path(__file__).resolve().parent
report=json.loads((p/'texture-provenance-tests.json').read_text());records=next(x['records'] for x in report['region_invocation_samples'] if x['scene']==143)
batch=(p/'object-replay-143-sampled-queue.bin').read_bytes();regions=[]
for qi in reversed(range(struct.unpack_from('<I',batch)[0])):
 record=struct.unpack_from('<8H',batch,8+qi*2068)
 if not record[5]&8:regions.append(record[0])
anchors=root_anchors(regions,records)
assert {r:anchors[r] for r in (16,18,17)}=={16:0,18:2,17:3}
rejected=0
for sample,rows in ((regions+[regions[0]],records),(regions[::-1],records),([r for r in regions if r!=21],records),(regions+[999],records),(regions,records+[records[0]])):
 try:root_anchors(sample,rows)
 except ValueError:rejected+=1
assert rejected==5
result=dict(result='PASS',regions=regions,anchors=anchors,rejected=rejected,scope='Unique root occurrences, preserved captured subsequence and following anchor only; no nested or within-block ordering inference.')
(p/'region-anchor-tests.json').write_text(json.dumps(result,indent=2));print(result)

