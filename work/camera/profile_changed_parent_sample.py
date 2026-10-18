from pathlib import Path
import time,json
from owned_thread_profile import ThreadProfile
exec(compile(Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0],'captured_scene_setup','exec'))
# Warm modules using a disposable pair, then profile a fresh uncached pair.
prepared.sample(.2020262778157515);prepared.close();history.close()
exec(compile(Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0],'captured_scene_setup','exec'))
profile=ThreadProfile();alpha=.2020262778157515
try:
 started=time.perf_counter_ns();result=profile.run(prepared.sample,alpha);elapsed=time.perf_counter_ns()-started
 assert result[0] and result[4]['geometry_records']>=0
 output=Path('work/camera/changed-parent-first-sample.thread-profile.json');profile.save(output)
 data=json.loads(output.read_text())
 print({'scope':'captured cold first sample; profiling overhead included, no live cadence claim','alpha':alpha,'elapsed_ms':elapsed/1e6,'top':[(r['function'],r['calls'],round(r['inclusive_wall_ns']/1e6,3)) for r in data['rows'][:18]]})
finally:prepared.close();history.close()
