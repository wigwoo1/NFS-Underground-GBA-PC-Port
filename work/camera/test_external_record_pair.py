import runpy,sys
from types import SimpleNamespace
from pathlib import Path
from owned_model_sources import OwnedModelSources
from owned_model_builder_inputs import OwnedModelBuilders
from owned_external_record_pair import prepare_external_record_pair
v=runpy.run_path('work/camera/test_external_record_candidate.py');scenes=[SimpleNamespace(graph=s,sources=OwnedModelSources.decode(Path(c['current-sources']).read_bytes(),s),builders=OwnedModelBuilders(Path(c['builders']).read_bytes())) for s,c in zip(v['scenes'],v['captures'])]
pair,visit,activation=prepare_external_record_pair(scenes,[v['portal'].sample(i) for i in (0,1)],v['frames'],v['rom'],1)
assert len(pair.older_blocks)==len(pair.newer_blocks)==12
assert len({visit.motion.matrix(i/100) for i in range(101)})==101
if len(sys.argv)<3:assert activation==1 and not pair.older_allocated and pair.newer_allocated
else:assert activation is None and pair.older_allocated and pair.newer_allocated
print('PASS complete external record/motion/visit pair; original activation',activation)
