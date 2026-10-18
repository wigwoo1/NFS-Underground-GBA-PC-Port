import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());a=[x['display_stats'] for x in r['checks']];assert len(a)==5 and len({x[9] for x in a})==1 and a[0][9]
assert all(len(x)==10 and x[1]==0 and x[0]==x[2]==i+1 for i,x in enumerate(a))
positive=[x for x in a if x[3]==0 and x[4]>0 and x[7]>0]
o=dict(result='PASS_SUBMISSION_COUNTS_DISPLAY_UNPROVEN',submissions=len(a),statistics_hresult=[hex(x[3]) for x in a],positive_display_records=len(positive),scope='GetLastPresentCount matches successful submissions. HRESULT success with zero PresentCount/QPC does not prove display. Hidden-window component only.')
Path(sys.argv[2]).write_text(json.dumps(o,indent=2));print(o)
