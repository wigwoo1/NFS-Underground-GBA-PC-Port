import json
from pathlib import Path
import owned_source_presentation_batch_candidate as batch
from owned_source_depth_transition_candidate import SourceFaceDeterminants
from owned_precomputed_source_samples_candidate import PrecomputedSourceWorldSamples
batch.SourceFaceDeterminants=SourceFaceDeterminants
source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')","folder=Path('work/camera/prototype-runs/fullscene-failure-1791566912183939000')")
ns={};samples=None
try:
 exec(compile(source,'capture_setup','exec'),ns)
 samples=PrecomputedSourceWorldSamples(ns['prepared'],(.2,.4,.6,.8))
 assert len(samples.samples)==4 and len(samples.source_masks)==4
 out=dict(result='PASS_CAPTURED_DEPTH_TRANSITION_SOURCE_REPLAY',alphas=list(samples.samples),source_mask_alphas=list(samples.source_masks),scope='Existing transition classifier permits captured failed pair through all four source precompute fractions; exact 54vertex negative-depth rejection demonstrated separately. No new visibility policy, full4K pixel comparison, live timing or original fractional fidelity claim.')
 Path('work/camera/prototype-runs/native-owner-depth-transition-replay-20261009.json').write_text(json.dumps(out,indent=2));print(out)
finally:
 if samples:samples.close()
 for k in ('prepared','history'):
  if ns.get(k):ns[k].close()
