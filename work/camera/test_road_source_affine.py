from pathlib import Path
import json
p=Path('work/camera');near=json.loads((p/'road-world-near-project-tests.json').read_text())['checks']
def affine_expected(mapping,g,source):
 rows=[]
 for r in mapping:
  a=next(x['attrs'] for x in near if x['source']==source and x['edge']==r['source_edge']) if r['near_generated'] else g['source_attributes'][r['source_vertex']]
  si=lambda x:((x+2**31)%2**32)-2**31
  rows.append([r['six_words'][0],r['six_words'][1],r['six_words'][3],si(a[0]<<(g['source_attributes_header'][1]+1)),si(a[1]*g['source_attributes_header'][2]*2)])
 return rows
s=(p/'test_road_source_ring.py').read_text();s=s.replace("matrix=bytes.fromhex", "raw=bytearray(raw);struct.pack_into('<I',raw,12,1);raw=bytes(raw)\n matrix=bytes.fromhex");s=s.replace("expected=[[r['six_words'][k] for k in (0,1,3,4,5)] for r in m['mapping']]","expected=affine_expected(m['mapping'],g,e['source'])");s=s.replace('road-source-ring-tests.json','road-source-affine-tests.json');s=s.replace('Integrated world/raw camera/near/project source-order emission, exact17 original endpoints; affine sources, preview invocation and GPU remain pending.','Affine UV lowword emission checked against original scaled raw source attrs at17 endpoints; q is geometric reciprocal, not original affine retained scratch q.');exec(compile(s,'affine_source_test','exec'),globals())
