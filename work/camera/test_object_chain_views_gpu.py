import runpy,json
from pathlib import Path
import owned_object_chain_views_candidate as candidate
candidate.install()
runpy.run_path('work/camera/test_combined_segmented_gpu.py',run_name='__main__')
r=json.loads(Path(__import__('sys').argv[2]).read_text());archive=json.loads(Path('work/camera/exact-pair-10331-4k.json').read_text());assert r['checks']==archive['checks'];assert candidate.calls>0
print('PASS archived10331 complete4K and chain calls',candidate.calls)
