"""Audit every saved sky sample; advancing phase alone is not pixel motion."""
import hashlib,json,sys
from pathlib import Path
src=Path(sys.argv[1]); dst=Path(sys.argv[2])
raw=src.read_bytes(); data=json.loads(raw); rows=data['samples']
assert len(rows)>=2
for i,row in enumerate(rows):
 assert row['index']==i and 0<=row['phase']<=1
 assert len(row['rgba_rgb_sha256'])==64
 assert all(c in '0123456789abcdef' for c in row['rgba_rgb_sha256'])
 if i: assert rows[i-1]['phase']<row['phase']
runs=[];start=0
for i in range(1,len(rows)+1):
 if i==len(rows) or rows[i]['rgba_rgb_sha256']!=rows[start]['rgba_rgb_sha256']:
  runs.append({'first_index':start,'last_index':i-1,'samples':i-start,'first_phase':rows[start]['phase'],'last_phase':rows[i-1]['phase']});start=i
holds=sum(a['rgba_rgb_sha256']==b['rgba_rgb_sha256'] for a,b in zip(rows,rows[1:]))
unique=len({r['rgba_rgb_sha256'] for r in rows})
assert data['unique_images']==unique
out={'result':'SAVED_SKY_PIXEL_HOLDS_CONFIRMED' if holds else 'NO_SAVED_ADJACENT_PIXEL_HOLDS','source':str(src.resolve()),'source_sha256':hashlib.sha256(raw).hexdigest(),'samples':len(rows),'adjacent_transitions':len(rows)-1,'unchanged_adjacent_images':holds,'changed_adjacent_images':len(rows)-1-holds,'unique_images':unique,'longest_identical_run_samples':max(r['samples'] for r in runs),'runs':runs,'scope':'Complete saved diagnostic image hashes only. No wall-clock cadence, current launcher selection, physical scanout, or spatial sky fidelity proof. An unchanged image may be legitimate for static sky; this moving captured angle pair requires further source reconstruction.'}
dst.write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in out.items() if k!='runs'},indent=2))
