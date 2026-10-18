"""Relate captured walls to the retained 16-byte visibility queue entries."""
from pathlib import Path
import json, struct
from scene_batches import batches
root=Path('work/camera')
capture=json.loads((root/'visibility-capture.json').read_text())
entries=next(s for s in capture['scenes'] if s['scene']==0)['entries']
rows=[]
for event in next(batches(root/'shading-spans.bin'))['events']:
    if event['pc']!=0x03000304:continue
    source=event['blocks'][5][0]
    bounds=list(struct.unpack_from('<4H',event['blocks'][1][1],0xe2))
    candidates=[e for e in entries if int(e['source'],16)<=source<int(e['source'],16)+e['source_count']*68
                and (source-int(e['source'],16))%68==0]
    matched=[e for e in candidates if e['fields'][1:5]==bounds]
    rows.append(dict(event=event['id'],source=hex(source),bounds=bounds,
                     candidate_entries=[e['index'] for e in candidates],matched_entries=[e['index'] for e in matched]))
report=dict(scene=0,walls=len(rows),bounds_matched=sum(bool(r['matched_entries']) for r in rows),walls_detail=rows,
            scope='Retained queue source ranges and bounds compared to captured wall calls. Does not prove queue construction or world-space visibility.')
(root/'visibility-queue-audit.json').write_text(json.dumps(report,indent=2))
print({k:v for k,v in report.items() if k!='walls_detail'})
for row in rows:
    if not row['matched_entries']:print(row)
