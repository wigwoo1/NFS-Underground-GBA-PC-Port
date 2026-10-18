import json
from pathlib import Path
a=json.loads(Path('prepared_hud_live_audit.json').read_text())
r=json.loads(Path(a['source']).read_text())
requests=r['world_preparation_stage_samples']
rows=[x for request in requests for x in request['parent_sample_rows']]
assert rows
early=[x for x in rows if x['ack_sent_ns']<=x['publication_begin_ns']<=x['published_ns']]
late=[x for x in rows if x['publication_begin_ns']<=x['published_ns']<=x['ack_sent_ns']]
out=dict(source=a['source'],sample_count=len(rows),early_count=len(early),late_count=len(late),
         selected_order_verified=len(early)==len(rows),cadence=a['coverage']['active_intervals'],
         scope='Actual per-sample acknowledgement timestamps distinguish selected order. Complete gameplay qualification remains separate.')
Path('early_ack_order_audit.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out))
assert out['selected_order_verified'],'Live preparation layer did not retain early acknowledgement order'
