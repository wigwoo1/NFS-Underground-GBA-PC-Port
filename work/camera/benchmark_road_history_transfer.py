"""Interleaved identical-source CPU comparison, independent of live/GPU scheduling."""
import runpy,time,statistics,json,hashlib,ctypes as C
from pathlib import Path
from owned_prepared_world_motion import PreparedWorldMotion
from owned_endpoint_road_planner import EndpointRoadPlanner
v=runpy.run_path('work/camera/audit_failed_world_motion.py');base=EndpointRoadPlanner(v['rom'],v['data']['table']);roads,_=base.plan(v['scenes'][0].graph);results={'transfer':[],'reconstruct':[]};fingerprints=set()
try:
 for trial in range(24):
  for mode in (('transfer','reconstruct') if trial%2==0 else ('reconstruct','transfer')):
   history=base.fork();prepared=None;advanced=None
   try:
    begin=time.perf_counter_ns();prepared=PreparedWorldMotion(*v['data']['frames'],*v['scenes'],history,roads,v['rom']);ready=time.perf_counter_ns()
    if mode=='transfer':
     advanced=prepared.take_next_history();history.close();history=advanced;advanced=None;new_roads=prepared.endpoint_roads[1]
    else:
     prepared.next_history.close();prepared.next_history=None;new_roads,_=history.plan(v['scenes'][1].graph)
    advanced_at=time.perf_counter_ns();digest=hashlib.sha256()
    for row in new_roads:digest.update(row['record'])
    for alpha in (0,.25,.5,.75,1):
     sample=prepared.sample(alpha);digest.update(sample[0])
     for buffer in sample[1:4]:
      if buffer is not None:digest.update(C.string_at(C.addressof(buffer),C.sizeof(buffer)))
    sampled=time.perf_counter_ns();fingerprints.add(digest.hexdigest());assert history.refresh==v['scenes'][1].graph.refresh
    if trial>=4:results[mode].append(dict(prepare_ms=(ready-begin)/1e6,advance_ms=(advanced_at-ready)/1e6,sample_ms=(sampled-advanced_at)/1e6,total_ms=(sampled-begin)/1e6))
   finally:
    if prepared:prepared.close()
    history.close()
    if advanced:advanced.close()
 assert len(fingerprints)==1,'History transfer changed complete scene bytes/poses/clips'
 report={'scope':'isolated CPU component benchmark; no gameplay/60fps certification','fixture':str(v['data']['folder']),'identical_scene_fingerprint':next(iter(fingerprints)),'trials_per_mode':20,'median_ms':{mode:{key:statistics.median(row[key] for row in rows) for key in rows[0]} for mode,rows in results.items()},'samples':results}
 output=Path('work/camera/prototype-runs')/('history-transfer-benchmark-'+str(time.time_ns())+'.json');output.write_text(json.dumps(report,indent=2));print(output);print(json.dumps(report['median_ms'],indent=2))
finally:base.close()
