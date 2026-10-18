from pathlib import Path
import json,struct
from scene_batches import records
p=Path('work/camera');old=list(records(p/'motion-original-draw-pages-world.bin'));new=list(records(p/'motion-original-initial-writes-world.bin'));filtered=[e for e in new if e['pc']!=0xffff0093];assert len(old)==len(filtered)
for a,b in zip(old,filtered):assert all(a[k]==b[k] for k in ('pc','frame','regs','blocks'))
checks=[]
for e in new:
 if e['pc']!=0xffff0093:continue
 raw=e['blocks'][93][1];overflow=struct.unpack('<I',e['blocks'][94][1])[0];assert overflow==0
 rows=[dict(pc=hex(w[0]),lr=hex(w[1]),stores=w[2],requested_bytes=w[3],first_address=hex(w[4]),end_address=hex(w[5]),first_refresh=w[6]) for w in struct.iter_unpack('<7I',raw)]
 checks.append(dict(refresh=e['frame'],producer_groups=sorted(rows,key=lambda r:-r['requested_bytes']),overflow=overflow))
r=dict(result='CAPTURED_INITIAL_PAGE_WRITE_PRODUCERS',existing_records_preserved=len(old),windows=len(checks),checks=checks,scope='Bounded original VRAM store PC/LR groups between display flips and first surface. Requested store sizes, not unique changed pixels; DMA may retain CPU PC. Full captured image producer inputs/native initialization unverified.')
(p/'motion-initial-write-producers.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print(r['result'],len(checks),len(old));print([(c['refresh'],[(v['pc'],v['requested_bytes']) for v in c['producer_groups'][:4]]) for c in checks])
