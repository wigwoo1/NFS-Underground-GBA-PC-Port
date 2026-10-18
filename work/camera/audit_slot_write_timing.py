"""Audit original allocation/deallocation instructions for a retained source identity."""
import json,struct,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());pose=Path(r['model_pose_trace']);raw=pose.with_suffix('.slots.bin').read_bytes();assert len(raw)%32==0
records=[struct.unpack_from('<8I',raw,i) for i in range(0,len(raw),32)]
assert all(h[0]==0x31534c4e and h[2] in (0x08023a16,0x080239ea,0x0801e49a,0x0801e4c2) and h[4]<=255 and h[5]<=255 for h in records)
# Identify source by original builder input model31, not arbitrary slot or screen polygon.
b=pose.with_suffix('.builders.bin').read_bytes();addresses={struct.unpack_from('<I',b,i+12)[0] for i in range(0,len(b),292) if struct.unpack_from('<h',b,i+32+54)[0]==31};assert len(addresses)==1
address=next(iter(addresses));changed=[h for h in records if h[3]==address and h[4]!=h[5]]
print(json.dumps({'source_address':address,'slot_writes':len(records),'source31_changes':[{'refresh':h[1],'pc':hex(h[2]),'older':h[4],'newer':h[5],'flags':h[7]} for h in changed if 10025<=h[1]<=10040]},indent=2))
assert any(10031<h[1]<=10035 and h[5]==255 and h[2] in (0x0801e49a,0x0801e4c2) for h in changed),'Expected source reset/removal not traced'
print('PASS: original source31 deallocation write inside verified source scene interval')

