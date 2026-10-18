import sys,json
from pathlib import Path
mode=sys.argv[1]
if mode=='candidate':
 import owned_road_asset_cache as assets
 from owned_road_material_resolution_candidate import road_candidates
 assets.road_candidates=road_candidates
output='work/camera/prototype-runs/road-material-resolution-4k-'+mode+'-20261009.json'
sys.argv=['fixture','work/camera/prototype-runs/owned-native-1791434872973979000.json',output]
source=Path('work/camera/test_owned_native_source_backdrop_batch_parity_candidate.py').read_text()
line=next(x for x in source.splitlines() if x.startswith('reference=json.loads'))
replacement="if mode=='candidate':\n reference=json.loads(Path('work/camera/prototype-runs/road-material-resolution-4k-baseline-20261009.json').read_text());assert [x['native_rgb_sha256'] for x in results]==[x['native_rgb_sha256'] for x in reference['frames']]"
source=source.replace(line,replacement)
exec(compile(source,'material_resolution_4k','exec'))
