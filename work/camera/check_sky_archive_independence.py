import json,hashlib
from pathlib import Path
p=Path('work/camera/prototype-runs')
names=['selected-sky-pixels-1791421521236581400.json','selected-sky-pixels-1791421795202590900.json']
rows=[json.loads((p/n).read_text())['records'] for n in names]
def payload(rs):
 return [dict(display_index=r['display_index'],epoch=r['epoch'],source_older=r['source_older'],refresh=r['refresh'],alpha=r['alpha'],fraction=r['fraction'],sha256=r['sha256'],points=[{k:pt[k] for k in ('x','y','actual','expected')} for pt in r['sky_reference_points']]) for r in rs]
a,b=map(payload,rows)
result=dict(files=names,records=[len(x) for x in rows],semantic_payload_equal=a==b,matching_payload_records=sum(x==y for x,y in zip(a,b)),stage_points=[sum('stage' in pt for r in rs for pt in r['sky_reference_points']) for rs in rows],first_thread=[rs[0]['thread'] for rs in rows],scope='Compare capture identities, fractional source phase and final pixel payloads; excludes optional stage values and thread/token metadata.')
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/final-sky-correspondence-20261008');(cp/'archive-independence.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
