"""Function profile of exact startup-ready scene replay; diagnostic times only."""
import sys,runpy,cProfile,pstats,json
from pathlib import Path
sys.path.insert(0,str(Path('work/camera').resolve()))
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-stall-exact-capture-20261008')
sys.argv=['replay_captured_preparation_ready.py',str(cp/'profiled-ready-replay.json'),str(cp/'scene-inputs'),'--candidate']
p=cProfile.Profile()
source=Path('work/camera/replay_captured_preparation_ready.py').read_text().replace('start=time.perf_counter_ns();cy=cycles();','profiler.enable();start=time.perf_counter_ns();cy=cycles();').replace('end=time.perf_counter_ns();ec=cycles()', 'end=time.perf_counter_ns();ec=cycles();profiler.disable()')
try:exec(compile(source,'profile_preparation_only','exec'),dict(__name__='__main__',profiler=p))
finally:p.disable();p.dump_stats(str(cp/'ready-preparation-functions.prof'))
stats=pstats.Stats(p)
rows=[dict(file=k[0],line=k[1],function=k[2],primitive_calls=v[0],calls=v[1],self_seconds=v[2],inclusive_seconds=v[3]) for k,v in stats.stats.items() if 'owned_' in k[0]]
rows.sort(key=lambda x:-x['self_seconds'])
(cp/'ready-preparation-functions.json').write_text(json.dumps(dict(scope='Only20round construct/precompute regions profiled; setup,signature verification and cleanup excluded. Profiler overhead. Inclusive times overlap. Self times prioritize inspection, not live-frame benchmarks.',functions=rows),indent=2))
print(json.dumps(rows[:12],indent=2))

