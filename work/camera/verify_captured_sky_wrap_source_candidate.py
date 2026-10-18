import json,sys,math
from pathlib import Path
from owned_sky_scroll import source_offset
r=json.loads(Path(sys.argv[1]).read_text());m=json.loads(Path(sys.argv[2]).read_text());assert len(m['rows'])==48 and not m['missed'] and not m['pending']
lookup={(x['epoch'],x['publication']):x for x in r['sky_capture_records']};assert len(lookup)==len(r['sky_capture_records'])
rows=[]
for x in m['rows']:
 a=lookup[x['epoch'],x['source_older']];b=lookup[x['epoch'],x['source_newer']]
 for q in (a,b):assert q['source']-q['asset_origin']==source_offset(q['angle'],240,0)
 assert a['asset_origin']==b['asset_origin'] and a['publication']<b['publication']
 delta=((b['angle']-a['angle']+8192)&16383)-8192;assert abs(delta*240/4096)<120
 phase=(((b['angle']&16383) if x['alpha']==1 else (a['angle']&16383)+delta*x['alpha'])*240/4096)%240
 assert math.isclose(phase-math.floor(phase),x['sky_weight'],abs_tol=1e-10)
 ap=((a['angle']&16383)*240/4096)%240;bp=((b['angle']&16383)*240/4096)%240
 rows.append(dict(identity=[x['epoch'],x['generation'],x['index']],older=a['publication'],newer=b['publication'],phase=phase,source_pair_wrap=abs(bp-ap)>120,y=x['y']))
out=dict(result='PASS_EXACT_CAPTURED_SKY_WRAP_SOURCE_PHASE',frames=len(rows),wrap_pair_frames=sum(x['source_pair_wrap'] for x in rows),wrap_pairs=sorted({(x['older'],x['newer']) for x in rows if x['source_pair_wrap']}),rows=rows,scope='Exact captured native endpoint identity to original sky pointer and continuous fraction; scoped to48 frames. Does not itself prove pixel fidelity or physical scanout cadence.')
assert out['wrap_pair_frames']>0,'Capture did not include any wrap pair'
Path(sys.argv[3]).write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='rows'}))
