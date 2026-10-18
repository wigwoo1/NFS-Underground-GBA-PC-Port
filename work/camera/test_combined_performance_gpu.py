import sys,types
from pathlib import Path
from owned_closed_viewport import ClosedViewport as OriginalViewport
oracle=types.ModuleType('_viewport_original_oracle');oracle.ClosedViewport=OriginalViewport;sys.modules['_viewport_original_oracle']=oracle
from install_combined_performance_candidate import install
install()
source=Path('work/camera/test_combined_validation_viewport_gpu.py').read_text().replace('from owned_closed_viewport import ClosedViewport as ReferenceViewport','from _viewport_original_oracle import ClosedViewport as ReferenceViewport')
exec(compile(source,'combined_performance_gpu','exec'))
