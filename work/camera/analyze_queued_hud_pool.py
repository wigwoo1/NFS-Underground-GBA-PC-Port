from pathlib import Path
import re,json
p=Path('work/camera');report=json.loads((p/'threaded-racing-motion-audit.json').read_text());prefix=Path(report['prefix']);rows=re.findall(r'owned_hud_pool full_bytes=(\d+) stored_bytes=(\d+) epoch=(\d+)',Path(str(prefix)+'-host.log').read_text());assert rows and all(int(e)>0 and 0<int(b)<=int(a)+720 for a,b,e in rows)
out=dict(result='QUEUED_HUD_POOL_STORAGE',owners=len(rows),full_equivalent_bytes=sum(int(a) for a,b,e in rows),pooled_bytes=sum(int(b) for a,b,e in rows),epochs=sorted({int(e) for a,b,e in rows}),scope='HUD allocation only, distinct producer owners; excludes remaining packet/source/road/text allocations and temporary capture full rows.')
(p/'owned-hud-pool-storage.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))

