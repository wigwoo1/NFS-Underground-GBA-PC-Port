import runpy,json,struct
from pathlib import Path
v=runpy.run_path('work/camera/test_external_fullscene_transition.py');p=v['prepared'].pair;record=p._scenery_record_pairs[1];rows=[]
for i in range(101):
 alpha=i/100;visit=p._external_visits[1].sample(alpha,p.portal.sample(alpha))
 if visit is None:continue
 left,right,top,bottom=visit['bounds'];rect=(left,top,right,bottom)
 rows.append(dict(alpha=alpha,rect=rect,rounded=tuple(round(x) for x in rect),fractional=any(x!=int(x) for x in rect)))
for alpha,blocks in ((0,record.older_blocks),(1,record.newer_blocks)):
 row=next(x for x in rows if x['alpha']==alpha);assert tuple(row['rect'])==struct.unpack('<4i',blocks[9])
result=dict(scope='source-owned opponent portal bounds; original endpoint model rect exact, intermediate precision audit only',rows=rows,fractional_samples=sum(x['fractional'] for x in rows),maximum_rounding_error=max(abs(a-b) for x in rows for a,b in zip(x['rect'],x['rounded'])))
out=Path('work/camera/prototype-runs/external-model-clip-precision.json');out.write_text(json.dumps(result,indent=2));print('PASS exact original model endpoint rectangles;',result['fractional_samples'],'fractional samples; max sourcepixel rounding error',result['maximum_rounding_error'])
