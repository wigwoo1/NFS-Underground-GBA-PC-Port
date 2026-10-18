import json,statistics
from pathlib import Path
p=Path('work/camera/prototype-runs')
q=json.loads((p/'source-gpu-timestamps-1791454549639373400.json').read_text());t=json.loads((p/'prepared-transfers-1791454551940503000.json').read_text())['rows']
assert q['stats'][0]==q['stats'][1]==2*len(q['rows']) and q['stats'][2]==0
queries={tuple(x[:3]):x for x in q['rows']};assert len(queries)==len(q['rows'])
joined=[]
for row in t:
 key=tuple(row[:3]);assert key in queries
 x=queries[key];assert x[6]==0 and x[7] in (1,3)
 if x[7]==1:assert x[4]>=x[3]
 lock=(row[5]-row[4])/1e6;unlock=(row[7]-row[6])/1e6
 joined.append(dict(identity=key,gpu_draw_ms=(x[4]-x[3])/1e6 if x[7]==1 else None,cpu_draw_ms=x[5]/1e6,interop_lock_ms=lock,interop_unlock_ms=unlock,query_state=x[7]))
gpu=[x['gpu_draw_ms'] for x in joined if x['gpu_draw_ms'] is not None]
slow=sorted(joined,key=lambda x:max(x['interop_lock_ms'],x['interop_unlock_ms']),reverse=True)
r=dict(result='PASS_EXACT_SOURCE_GPU_PREPARE_JOIN',draws=len(queries),transfers=len(joined),draws_without_transfer=len(queries)-len(joined),resolved=sum(x[7]==1 for x in q['rows']),canceled=sum(x[7]==3 for x in q['rows']),query_stats=q['stats'],gpu_draw_median_ms=statistics.median(gpu),gpu_draw_max_ms=max(gpu),over20ms_interop=sum(max(x['interop_lock_ms'],x['interop_unlock_ms'])>20 for x in joined),top_stalls=slow[:10],scope='Exact identity, GPU clock interval includes scheduling; does not isolate blit, interop scheduling or external load. CPU/GPU timestamps are separate clock domains.')
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/source-timestamp-live-20261008');(cp/'source-gpu-join.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
