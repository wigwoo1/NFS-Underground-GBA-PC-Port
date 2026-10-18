"""Exact captured replay through contiguous source sample class, not segmented."""
from pathlib import Path
p=Path('work/camera/replay_captured_preparation_ready.py');s=p.read_text()
assert s.count('assembly.join_frame=SegmentedFrame.join')==1
assert s.count('from owned_precomputed_segmented_samples import PrecomputedSourceWorldSamples')==1
s=s.replace('assembly.join_frame=SegmentedFrame.join','# Keep original contiguous assembly.join_frame')
s=s.replace('from owned_precomputed_segmented_samples import PrecomputedSourceWorldSamples','from owned_precomputed_source_samples_candidate import PrecomputedSourceWorldSamples')
exec(compile(s,str(p),'exec'))
