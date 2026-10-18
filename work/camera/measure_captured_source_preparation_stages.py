import sys,json,time
from pathlib import Path
from owned_road_record_diagnostic import decode
from owned_road_history_diagnostic import restore,snapshot
from owned_sample_signature import signature
report=json.loads(Path(sys.argv[1]).read_text());meta=report['live_preparation_profiles'][0];folder=Path(meta['capture'])
source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')",'folder=Path('+repr(str(folder))+')')
exec(compile(source,'captured_scene_setup','exec'));prepared.close();history.close()
h=json.loads((folder/'road-history.json').read_text());roads=decode(json.loads((folder/'older-roads.json').read_text()));expected=json.loads((folder/'prepared-signatures.json').read_text())

import statistics
import owned_closed_scene_memory as memory
from owned_precomputed_source_samples_candidate import PrecomputedSourceWorldSamples
from owned_wall_visibility_candidate import helper
from sample_owned_motion import rigid_library
import owned_sampled_world_frame as assembly
native_join=any(stage.get('frame_join_trace') is not None for job in report['world_preparation_stage_samples'] for sample in job.get('sample_timings',[]) for stage in sample.get('assembly_stages',[]) if stage.get('name')=='immutable_frame_join')
if native_join:
 from owned_native_frame_join import join_frame,trace,helper as join_helper
 join_helper();assembly.join_frame=join_frame;assembly.join_frame_trace=trace
helper();rigid_library();rows=[]
for trial in range(9):
 memory._scene_memory_local.entries=[]
 history=EndpointRoadPlanner(rom,table);history.scratch=restore(history.d,h['scratch']);history.epoch=h['epoch'];history.refresh=h['refresh'];prepared=None;cached=None
 try:
  started=time.perf_counter_ns();prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom);constructed=time.perf_counter_ns()
  cached=PrecomputedSourceWorldSamples(prepared,tuple(x['alpha'] for x in expected),trace=True);completed=time.perf_counter_ns()
  actual=json.loads(json.dumps([dict(alpha=x['alpha'],signature=signature(cached.sample(x['alpha']))) for x in expected]));assert actual==expected,'Exact source replay mismatch'
  assembly={};source_stages={};wall_selection={}
  for sample in cached.sample_timings:
   for stage in sample['assembly_stages']:
    assembly[stage['name']]=assembly.get(stage['name'],0)+stage['wall_ns']/1e6
    for sub in stage.get('visibility_stages',[]):wall_selection[sub['name']]=wall_selection.get(sub['name'],0)+sub['wall_ns']/1e6
   for stage in sample['source_sample_stages']:source_stages[stage['name']]=source_stages.get(stage['name'],0)+stage['wall_ns']/1e6
  rows.append(dict(trial=trial,construct_ms=(constructed-started)/1e6,precompute_ms=(completed-constructed)/1e6,assembly_ms=assembly,source_ms=source_stages,wall_selection_ms=wall_selection))
 finally:
  if cached is not None:cached.close()
  if prepared is not None:prepared.close()
  history.close()
measured=rows[1:]
def med(group):
 keys={k for row in measured for k in row[group]};return {k:statistics.median(row[group].get(k,0) for row in measured) for k in sorted(keys)}
result=dict(result='PASS_EXACT_SOURCE_STAGE_REPLAY',samples=len(expected)*len(rows),native_frame_join=native_join,construct_median_ms=statistics.median(row['construct_ms'] for row in measured),precompute_median_ms=statistics.median(row['precompute_ms'] for row in measured),assembly_median_ms=med('assembly_ms'),source_median_ms=med('source_ms'),wall_selection_median_ms=med('wall_selection_ms'),trials=rows,scope='Same captured scene/history/roads, nine complete source replays; first trial omitted from medians. Existing bounded transform caches may warm; inclusive nested stage timings overlap and exclude GPU/live cadence.')
Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='trials'},indent=2))
