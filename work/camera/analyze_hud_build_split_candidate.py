import json,statistics,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());rows=[x['prepared']['hud_build_split'] for x in r['presentation_samples'] if x.get('native_result')==1 and 'hud_build_split' in x.get('prepared',{})];assert rows
for x in rows:assert len(x)==8 and sum(x[2:7])<=x[7],x
fields={'text':2,'vram_copy_window':3,'sprite_decode':4,'output':5,'cache_publish':6,'total':7}
groups={}
for reuse in [False,True]:
 selected=[x for x in rows if bool(x[0])==reuse]
 groups['reused' if reuse else 'rebuilt']={key:dict(count=len(selected),median_ms=statistics.median(x[col] for x in selected)/1e6,max_ms=max(x[col] for x in selected)/1e6) for key,col in fields.items()} if selected else {}
out=dict(result='PASS_RETAINED_NATIVE_HUD_BUILD_SPLIT_ACCOUNTING',groups=groups,scope='Retained successful native rebuild wall intervals; perrowQPCprobes perturb timing, remaining cycles not split. Stage medians cannot be summed as median total; no causal memory or fullscene60proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
