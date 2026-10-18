import json,sys,statistics
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());rows=[x for x in r['presentation_samples'] if x.get('native_result')==1]
values=[]
for x in rows:
 p=x['prepared'];t=x['callback_timing'];draw=t['draw_end_ns']-t['draw_begin_ns'];source=p['source_prepare_ns'];consumer=sum(v['elapsed_ns'] for v in p['consumer_stages']);assert draw>=0 and source>=0 and consumer>=0
 values.append(dict(draw=draw,source=source,consumer=consumer,unaccounted=draw-source-consumer))
def stats(k):
 v=[x[k]/1e6 for x in values];return dict(count=len(v),median_ms=statistics.median(v),min_ms=min(v),max_ms=max(v))
out=dict(result='RETAINED_SKY_DRAW_ACCOUNTING',**{k:stats(k) for k in values[0]},negative_residuals=sum(x['unaccounted']<0 for x in values),scope='Retained successful draw callbacks only. Residual includes dispatch, waits, scheduling and uninstrumented work; not causal attribution. Stage medians do not add to median total.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
