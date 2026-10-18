"""Join disjoint presentation stalls to completed original preparation pairs."""
import json,sys
from pathlib import Path
from analyze_consumer_gap_partition import analyze
rp,op=map(Path,sys.argv[1:3]);r=json.loads(rp.read_text());part=analyze(r);rows={x['display_index']:x for x in r['presentation_samples'] if 'display_index' in x}
for g in part['largest']:
 x=rows[g['display_index']];candidates=[s for s in r['world_preparation_stage_samples'] if s['older']==x['source_older'] and s['newer']==x['refresh'] and s['completed_ns']<=x['pair_ready_ns']];assert candidates
 s=max(candidates,key=lambda s:s['completed_ns']);g['preparation']=dict(older=s['older'],newer=s['newer'],unfinished_at_acquire_ms=max(0,s['completed_ns']-x['pair_begin_ns'])/1e6,completion_to_acquired_ms=(x['pair_ready_ns']-s['completed_ns'])/1e6,stages=s)
part['measurement_scope']='Captured preparation intervals may include profiling, diagnostic input serialization and signature hashing. Inspect world preparation profiles before using wall times as normal gameplay cost.'
op.write_text(json.dumps(part,indent=2));print(json.dumps([{k:v for k,v in g.items() if k not in ('parts','preparation')}|dict(preparation={k:v for k,v in g['preparation'].items() if k!='stages'},stage_keys=list(g['preparation']['stages'])) for g in part['largest'][:3]],indent=2))

