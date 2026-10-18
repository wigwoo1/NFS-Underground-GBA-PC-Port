"""Identify later queued draws inside a sample's draw-to-commit interval."""
import json,sys
from pathlib import Path
from analyze_consumer_gap_partition import analyze
r=json.loads(Path(sys.argv[1]).read_text());g=analyze(r);rows={x['display_index']:x for x in r['presentation_samples'] if x.get('native_committed_sample')};out=[]
for gap in g['largest']:
 x=rows[gap['display_index']];q=x['queued_stage_timing'];wait=x['native_wait_timing'];begin=q[1];end=wait[0];siblings=[]
 for y in rows.values():
  if y.get('batch_native_call_ns')!=x.get('batch_native_call_ns'):continue
  t=y.get('queued_stage_timing');a=max(begin,t[0]);b=min(end,t[1])
  if b>a:siblings.append(dict(display_index=y['display_index'],position=y['batch_sample_position'],begin_ns=a,end_ns=b,overlap_ms=(b-a)/1e6))
 ordered=sorted(siblings,key=lambda s:s['begin_ns']);last=begin;total=0
 for s in ordered:total+=max(0,s['end_ns']-max(last,s['begin_ns']));last=max(last,s['end_ns'])
 out.append(dict(display_index=x['display_index'],gap_ms=gap['gap_ms'],draw_to_wait_ms=(end-begin)/1e6,other_draw_union_ms=total/1e6,remainder_ms=(end-begin-total)/1e6,siblings=siblings))
result=dict(result='PASS_QUEUED_DRAW_OVERLAP',largest=out,scope='Queued bridge draws up to three frames before committing the first. Draw-to-wait includes later full-scene draws, acquire/probe/readiness and scheduling; remainder not exclusive cause. No frame dropping or timing fix claimed.')
Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print(json.dumps(out[:1],indent=2))
