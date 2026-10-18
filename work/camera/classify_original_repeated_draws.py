from pathlib import Path
from collections import defaultdict
import json
p=Path(__file__).resolve().parent;report=json.loads((p/'recursive-draw-corpus-audit.json').read_text());assert len(report['cases'])==202 and all(c['exact'] for c in report['cases']);groups=[]
for case in report['cases']:
 label=case['label'];native=json.loads((p/'recursive-draw-corpus'/(label+'-native.json')).read_text());by=defaultdict(list)
 for i,row in enumerate(native['native']):by[(row['kind'],row['source'])].append(i)
 for key,indices in by.items():
  if len(indices)<2:continue
  rows=[native['native'][i] for i in indices];signatures={(r['record'],r['pass_value'],tuple(r['bounds'])) for r in rows};groups.append(dict(case=label,kind=key[0],source=key[1],indices=indices,draws=len(indices),distinct_record_pass_clip=len(signatures),record_pass_clip_unique=len(signatures)==len(rows)))
result=dict(result='CLASSIFIED_ORIGINAL_MATCHED_REPEATS',cases=202,groups=len(groups),draws_in_repeat_groups=sum(g['draws'] for g in groups),groups_needing_invocation_identity=sum(not g['record_pass_clip_unique'] for g in groups),details=groups,scope='Every grouped native world draw already matched original source/order/record/pass/visibleclip and resolved inputs; equal record/pass/clip still needs original invocation identity, not deduplication.')
(p/'original-repeat-classification.json').write_text(json.dumps(result,indent=2));print({k:v for k,v in result.items() if k!='details'})
