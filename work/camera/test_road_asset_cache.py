from pathlib import Path
from dataclasses import replace
import json
from owned_closed_graph import ClosedGraph
from owned_road_asset_cache import RoadAssetCache
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());rows=r['wall_diagnostic_frames']
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
cache=RoadAssetCache(rom)
a=ClosedGraph.decode(Path(rows[0]['graph']).read_bytes());first=cache.get(a);equivalent=ClosedGraph.decode(Path(rows[0]['graph']).read_bytes());again=cache.get(equivalent)
assert again[0] is equivalent and again[2] is first[2] and again[3] is first[3] and cache.hits==1
changed=replace(a,callbacks=a.callbacks+b'changed-owner');different=cache.get(changed);assert different[2] is not first[2] and cache.misses==2
branch=cache.fork();branch.clear();assert len(cache.entries)==2 and not branch.entries
for row in rows[1:]:
 scene=ClosedGraph.decode(Path(row['graph']).read_bytes());cache.get(scene);assert len(cache.entries)<=2 and cache.bytes<=cache.budget
cache.clear();assert cache.bytes==0 and not cache.entries
cache.budget=0;cache.get(a);assert not cache.entries and cache.bytes==0
print('PASS exact-content reuse, changed-owner miss, fork/close isolation, 16-scene bounded retention, oversized bypass')
