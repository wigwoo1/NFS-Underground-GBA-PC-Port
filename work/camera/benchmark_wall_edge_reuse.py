"""Balanced exact-scene candidate comparison with independent saved signatures."""
import sys,json,statistics
from pathlib import Path
import owned_sampled_graph_gpu as gpu
from owned_wall_edge_reuse_candidate import selected_graph_walls
baseline=gpu.selected_graph_walls
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-stall-exact-capture-20261008')
sys.argv=['replay',str(cp/'edge-reuse-balanced.json'),str(cp/'scene-inputs'),'--candidate']
s=Path('work/camera/replay_captured_preparation_ready.py').read_text()
s=s.replace('for i in range(20):','for i in range(40):\n gpu.selected_graph_walls=baseline if i%4 in (0,3) else selected_graph_walls')
s=s.replace('rows.append(dict(round=i,','rows.append(dict(candidate=i%4 in (1,2),round=i,')
exec(compile(s,'balanced_edge_reuse','exec'),globals())
r=json.loads((cp/'edge-reuse-balanced.json').read_text());summary={}
for mode in (False,True):
 rows=[x for x in r['rounds'][8:] if x['candidate']==mode]
 summary[str(mode)]=dict(rounds=len(rows),median_precompute_ms=statistics.median(x['precompute_ms'] for x in rows),median_construct_ms=statistics.median(x['construct_ms'] for x in rows))
r['balanced_summary']=summary;r['scope']+=' ABBA alternating per-selection edge reuse, first8rounds excluded.'
(cp/'edge-reuse-balanced.json').write_text(json.dumps(r,indent=2));print(summary)
