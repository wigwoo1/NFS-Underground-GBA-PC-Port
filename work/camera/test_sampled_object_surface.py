"""Regenerated static object90 surface versus retained packet source payload."""
from pathlib import Path
import json,struct,hashlib
p=Path('work/camera');packet=(p/'overflow-scene-171/old.bin').read_bytes();sections={t:packet[o:o+n] for t,o,n in (struct.unpack_from('<3I',packet,32+i*12) for i in range(5))}
cursor=8;captured=None;matches=0
for i in range(struct.unpack_from('<I',sections[2],4)[0]):
 n,w,h=struct.unpack_from('<3I',sections[2],cursor);size=12+n*40+w*h*4;identity=struct.unpack_from('<5I',sections[5],8+i*20)
 if identity[2]==139938876:captured=sections[2][cursor:cursor+size];matches+=1
 cursor+=size
assert matches==1
cases=[]
for a in ('0.25','0.5','0.75'):
 report=json.loads((p/f'sampled-object-dispatch-{a}-motion-tests.json').read_text());surfaces=report['object_surfaces'];assert len(surfaces)==1
 entry=surfaces[0];assert entry['source']==139938876 and entry['extracted'] and entry['stage']==0
 raw=(p/f'sampled-object-surface-{a}-motion.bin').read_bytes();assert raw==captured and hashlib.sha256(raw).hexdigest()==entry['sha256']
 draw=next(v for v in report['draws'] if v['source']==139938876);call=report['calls'][draw['owner']]
 assert call['region']==90 and call['object']==33573732 and call['caller']==0x03002364
 cases.append(dict(alpha=float(a),bytes=len(raw),bounds=call['record'][1:5],geometry_uv_rgba_exact=True))
report=dict(result='PASS',source=139938876,cases=cases,scope='Static object90 source regenerated during sampled original dispatch. Complete payload exact against retained draw; model palette suffices for this asset only. No moving object90 transform, generalized palette selection, full scene or timing proof.')
(p/'sampled-object-surface-tests.json').write_text(json.dumps(report,indent=2));print(report)
