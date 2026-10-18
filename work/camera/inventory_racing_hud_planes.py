import hashlib,json,sys
from pathlib import Path
rows=[]
for p in Path('work/camera/prototype-runs').glob('racing-motion*hud.bin'):
 b=p.read_bytes(); assert len(b)==5591040
 counts=[len({b[r*34944+off:r*34944+off+size] for r in range(160)}) for off,size in [(128,32768),(32896,1024),(33920,1024)]]
 rows.append({'path':str(p),'counts':counts,'payload_bytes':counts[0]*32768+(counts[1]+counts[2])*1024,'sha256':hashlib.sha256(b).hexdigest()})
assert rows
rows.sort(key=lambda x:x['payload_bytes'],reverse=True)
print(json.dumps({'scope':'Exact unique full-plane bytes in retained racing fixtures; not live cost','fixtures':rows},indent=2))
