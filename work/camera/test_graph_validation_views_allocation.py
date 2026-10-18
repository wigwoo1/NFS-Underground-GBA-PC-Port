import tracemalloc,json
from pathlib import Path
from owned_closed_graph_validation_views_candidate import install,uninstall
from owned_scene_process_transport import unpack
ns={};exec(Path('work/camera/profile_complete_scene_unpack_candidate.py').read_text().split('for iteration in range(8):')[0],ns);rows=[]
for label in ('baseline','candidate','candidate','baseline'):
 (install if label=='candidate' else uninstall)();tracemalloc.start();decoded=[unpack(p,ns['rom']) for p in ns['packets']];current,peak=tracemalloc.get_traced_memory();tracemalloc.stop();rows.append(dict(label=label,retained_bytes=current,peak_bytes=peak));del decoded
uninstall();cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/graph-validation-views-20261010');(cp/'allocation.json').write_text(json.dumps(dict(rows=rows,scope='Two decoded private captured endpoints; Python traced allocations only, tracing perturbs timing. No native/GPU allocation or live cadence claim.'),indent=2));print(rows)
