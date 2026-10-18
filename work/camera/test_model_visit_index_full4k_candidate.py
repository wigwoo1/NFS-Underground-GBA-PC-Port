import sys,json
from pathlib import Path
import owned_model_visit_index_install_candidate
sys.argv=['fixture','work/camera/prototype-runs/owned-native-1791434872973979000.json','work/camera/prototype-runs/model-visit-index-full4k-parity.json']
source=Path('work/camera/test_owned_native_source_backdrop_batch_parity_candidate.py').read_text()
line=next(x for x in source.splitlines() if x.startswith('reference=json.loads'))
source=source.replace(line,"reference=json.loads(Path('work/camera/prototype-runs/scene-merge-current-baseline.json').read_text());assert [x['native_rgb_sha256'] for x in results]==[x['native_rgb_sha256'] for x in reference['frames']]")
exec(compile(source,'scene-merge-full4k-fixture','exec'))

assert owned_model_visit_index_install_candidate.stats['calls']>0
report=Path('work/camera/prototype-runs/model-visit-index-full4k-parity.json');data=json.loads(report.read_text());data['model_visit_index_selection']=dict(owned_model_visit_index_install_candidate.stats);report.write_text(json.dumps(data,indent=2));print(data['model_visit_index_selection'])
