"""Inventory both bytes of recovered road texels; no screen geometry fitting."""
from pathlib import Path
import struct,json,hashlib
from scene_batches import records
p=Path('work/camera');source=p/'world.bin';checks=[]
for e in records(source):
 if e['pc']!=0x030032f0:continue
 b=e['blocks'];packed=b[66][1]
 if not packed:continue
 mat=b[8][1];width=1<<struct.unpack_from('<H',mat,36)[0];height=struct.unpack_from('<H',mat,38)[0]//2
 assert len(packed)==width*height*2
 decoded=b''.join(packed[y*width*2:y*width*2+width] for y in range(height))
 # Original U mask covers width/2 halfwords per row, each containing two indices.
 pairs=[(packed[y*width*2+2*x],packed[y*width*2+2*x+1]) for y in range(height) for x in range(width//2)]
 assert bytes(v for pair in pairs for v in pair)==decoded
 different=sum(a!=c for a,c in pairs)
 checks.append(dict(event=e['id'],width=width,height=height,pairs=len(pairs),different_lane_pairs=different,decoded_sha256=hashlib.sha256(decoded).hexdigest(),both_lanes_preserved=True,sha256=hashlib.sha256(packed).hexdigest()))
assert checks
report=dict(result='MEASURED',source=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),events=len(checks),events_with_different_lanes=sum(c['different_lane_pairs']>0 for c in checks),checks=checks,scope='Addressable rows only, padding excluded. Native byte-wide extraction preserves BOTH lanes of every original addressable halfword; no missing-lane decoder bug is established. Original screen pair sampling couples the two output lanes to one UV; ordinary continuous GPU UV sampling does not enforce that coupling. Investigate this sampling distinction and perspective subdivision using native geometry; this inventory does not prove a live-scene cause or authorize screen-span reconstruction.')
(p/'road-packed-lane-inventory.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k!='checks'})
