import json,statistics
from pathlib import Path
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/vertex-conversion-profile-20261010')
r=json.loads((cp/'live10-raw.json').read_text());conversions=json.loads((cp/'conversions.json').read_text());rows=[];used=set()
for x in r['presentation_samples']:
 p=x['prepared'];b=p['bundle_transfer_profile'];calls=p['d3d_call_profiles'];assert calls
 end=calls[0]['caller_begin_ns']
 selected=[(i,c) for i,c in enumerate(conversions) if b['caller_end_ns']<=c['begin_ns']<=c['end_ns']<=end]
 assert len(selected)==1
 i,c=selected[0];assert i not in used;used.add(i)
 stages={s['stage']:s['elapsed_ns']/1e6 for s in p['consumer_stages']}
 assert 'vertices_copy_convert' in stages and 'source_bundle_copy' in stages
 dt=(c['end_ns']-c['begin_ns'])/1e6
 dispatch=p['renderer_dispatch']
 rows.append(dict(pair=[x['source_older'],x['refresh']],index=x['display_index'],conversion_ms=dt,conversion_stage_ms=stages['vertices_copy_convert'],conversion_stage_other_ms=stages['vertices_copy_convert']-dt,native_copy_ms=(b['native_end_ns']-b['native_begin_ns'])/1e6,copy_stage_ms=stages['source_bundle_copy'],copy_stage_other_ms=stages['source_bundle_copy']-(b['native_end_ns']-b['native_begin_ns'])/1e6,render_stage_sum_ms=sum(stages.values()),prepare_dispatch_ms=(dispatch['completed_ns']-dispatch['started_ns'])/1e6,source_prepare_ms=p['source_prepare_ns']/1e6))
 assert rows[-1]['conversion_stage_other_ms']>=0 and rows[-1]['copy_stage_other_ms']>=0
keys=[k for k in rows[0] if k.endswith('_ms')]
out=dict(result='PASS_UNIQUE_VERTEX_COPY_STAGE_RECONCILIATION',count=len(rows),summary={k:dict(median=statistics.median(x[k] for x in rows),maximum=max(x[k] for x in rows)) for k in keys},worst_dispatch=sorted(rows,key=lambda x:x['prepare_dispatch_ms'],reverse=True)[:8],rows=rows,scope='Last120 actual presentation records; unique conversion between copy return and first material call. Stages separately named by actual active installer; elapsed includes scheduling and overlapping source timings, no exclusive CPU claim.')
(cp/'stage-reconciliation.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k not in ('rows','worst_dispatch')},indent=2))
