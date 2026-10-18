import json,struct
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_closed_scene_memory import ClosedSceneMemory
from owned_complete_road_candidates import road_candidates
from owned_endpoint_road_selection import endpoint_road_span_candidates
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);reference=json.loads(Path('work/camera/owned-road-region-identity-tests.json').read_text());checks=[]
for f,expected in zip(r['wall_diagnostic_frames'],reference['checks']):
 c=ClosedGraph.decode(Path(f['graph']).read_bytes());m=ClosedSceneMemory(c,rom);selected=endpoint_road_span_candidates(c,m,road_candidates(c,m),table);actual=[(x['descriptor'],x['ordinal'],tuple(x['bounds'])) for x in selected];wanted=[(x['descriptor'],x['ordinal'],tuple(x['bounds'])) for x in expected['roads']]
 extras=[x for x in actual if x not in wanted]
 checks.append(dict(refresh=c.refresh,exact=actual==wanted,extra_span_candidates=extras,missing_captured_candidates=[x for x in wanted if x not in actual],roads=[{k:v for k,v in x.items() if k!='source'} for x in selected]))
out=dict(result='AUDIT_ENDPOINT_ROAD_SPAN_CANDIDATES',checks=checks,scope='Recovered original endpoint geometry/horizontal clipping/span selection independent of draw record matching; extra span candidates require actual source-run submission predicate before verified selection')
Path('work/camera/endpoint-road-selection-tests.json').write_text(json.dumps(out,indent=2));print(out['result'],sum(len(x['roads']) for x in checks))
