"""Account live callback duration against measured native preparation stages."""
import json,sys,statistics
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());rows=[x for x in r['presentation_samples'] if x['native_result']==1];records=[]
for i,x in enumerate(rows):
 t=x['callback_timing'];p=x['prepared'];source=p['source_prepare_ns'];stages={s['stage']:s['elapsed_ns'] for s in p['consumer_stages']};draw=t['draw_end_ns']-t['draw_begin_ns'];measured=source+sum(stages.values());prev=rows[i-1] if i else None
 records.append(dict(index=x['display_index'],pair_boundary=prev is not None and (x['source_older'],x['refresh'])!=(prev['source_older'],prev['refresh']),draw_ms=draw/1e6,source_ms=source/1e6,consumer_ms=sum(stages.values())/1e6,unaccounted_ms=(draw-measured)/1e6,stages_ms={k:v/1e6 for k,v in stages.items()}))
def summary(xs):
 return dict(count=len(xs),**{k:dict(median=statistics.median(x[k] for x in xs),maximum=max(x[k] for x in xs)) for k in ('draw_ms','source_ms','consumer_ms','unaccounted_ms')}) if xs else dict(count=0)
out=dict(result='NATIVE_PREPARATION_ACCOUNTING',all=summary(records),pair_boundary=summary([x for x in records if x['pair_boundary']]),within_pair=summary([x for x in records if not x['pair_boundary']]),slow_draws=summary([x for x in records if x['draw_ms']>20]),records=records,scope='Wall durations include scheduling and GIL waits. Unaccounted remainder includes queue handoff and uninstrumented work, not proof of a specific cause. CPU/API metadata, no scanout proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='records'})
