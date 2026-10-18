"""Isolated segmented/single queued sky-buffer reuse live candidate."""
from pathlib import Path
from install_combined_performance_candidate import install
install()
p=Path('work/camera/run_segmented_wait_profile_candidate.py');s=p.read_text()
assert s.count('owned-gpu-segmented-source-candidate.dll')==1
s=s.replace('owned-batch-queued-wait-profile-candidate.dll','owned-batch-queued-single-candidate.dll').replace('owned-gpu-segmented-source-candidate.dll','owned-gpu-segmented-sky-buffer-candidate.dll')
s=s.replace(" path=Path('work/camera/prototype-runs')", " stats=(C.c_uint64*2)();gpu.nf_sky_vertex_buffer_stats.argtypes=[C.c_void_p]\n assert gpu.nf_sky_vertex_buffer_stats(stats) and stats[0]==0 and stats[1]>=1\n path=Path('work/camera/prototype-runs')")
s=s.replace('dict(targets=list(targets),fences=list(fences))','dict(targets=list(targets),fences=list(fences),sky_vertex_buffer_stats=list(stats))')
exec(compile(s,str(p),'exec'))
