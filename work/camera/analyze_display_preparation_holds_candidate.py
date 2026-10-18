"""Associate complete reported display holds with exact retained preparation gaps."""
import json,sys
from pathlib import Path
raw=Path(sys.argv[1]);r=json.loads(raw.read_text())
a=json.loads(raw.with_name(raw.stem+'-preparation-wait-audit.json').read_text())
assert r['dxgi_display_progress']['excess_refresh_spans_dropped']==0
rows=[]
for span in r['dxgi_display_progress']['excess_refresh_spans']:
 old,new=span['older_native_sample'],span['newer_native_sample'];assert old and new
 identity=[new['epoch'],new['generation'],new['display_index']]
 assert identity[:2]==span['key'] and new['display_index']>old['display_index']
 matches=[x for x in a['rows'] if x['identity']==identity];assert len(matches)<=1
 rows.append(dict(identity=identity,reported_hold_ms=(span['end_qpc']-span['start_qpc'])*1000/span['qpc_frequency'],image_advance=span['image_advance'],refresh_advance=span['refresh_advance'],native_partition=matches[0] if matches else None))
out=dict(result='PASS_REPORTED_DISPLAY_PREPARATION_ASSOCIATIONS',rows=rows,scope='Reported display-owner association and zero-drop >25ms native interval partition; absent partition means below-threshold detail, not absence of hold. No exclusive CPU/GC cause or physical scanout proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out)
