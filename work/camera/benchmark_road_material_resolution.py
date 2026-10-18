"""Balanced exact-scene candidate comparison with independent saved signatures."""
import sys,json,statistics
from pathlib import Path
import owned_complete_road_candidates as gpu
from owned_road_material_resolution_candidate import road_candidates as selected_graph_walls
baseline=gpu.road_candidates
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-stall-exact-capture-20261008')
sys.argv=['replay',str(cp/'road-material-balanced.json'),str(cp/'scene-inputs'),'--candidate']
s=Path('work/camera/replay_captured_preparation_ready.py').read_text()
s=s.replace('for i in range(20):','for i in range(40):\n chosen=baseline if i%4 in (0,3) else selected_graph_walls\n for module in tuple(sys.modules.values()):\n  if module is not None and getattr(module,\"road_candidates\",None) in (baseline,selected_graph_walls):setattr(module,\"road_candidates\",chosen)')
s=s.replace('rows.append(dict(round=i,','rows.append(dict(candidate=i%4 in (1,2),round=i,')
exec(compile(s,'balanced_edge_reuse','exec'),globals())
r=json.loads((cp/'road-material-balanced.json').read_text());summary={}
for mode in (False,True):
 rows=[x for x in r['rounds'][8:] if x['candidate']==mode]
 summary[str(mode)]=dict(rounds=len(rows),median_precompute_ms=statistics.median(x['precompute_ms'] for x in rows),median_construct_ms=statistics.median(x['construct_ms'] for x in rows))
r['balanced_summary']=summary;r['scope']+=' ABBA alternating per-decode successful road material reuse, first8rounds excluded.'
(cp/'road-material-balanced.json').write_text(json.dumps(r,indent=2));print(summary)


