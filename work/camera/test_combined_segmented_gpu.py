"""Exercise live segmented precomputation class with aggregate overrides and original GPU oracle."""
import sys,types
from pathlib import Path
from owned_closed_viewport import ClosedViewport as OriginalViewport
oracle=types.ModuleType('_viewport_original_oracle');oracle.ClosedViewport=OriginalViewport;sys.modules['_viewport_original_oracle']=oracle
from install_combined_performance_candidate import install
install()
import owned_precomputed_source_samples_candidate as original_precompute
from owned_precomputed_segmented_samples import PrecomputedSourceWorldSamples
original_precompute.PrecomputedSourceWorldSamples=PrecomputedSourceWorldSamples
source=Path('work/camera/test_combined_validation_viewport_gpu.py').read_text().replace('from owned_closed_viewport import ClosedViewport as ReferenceViewport','from _viewport_original_oracle import ClosedViewport as ReferenceViewport')
exec(compile(source,'combined_segmented_gpu','exec'))
