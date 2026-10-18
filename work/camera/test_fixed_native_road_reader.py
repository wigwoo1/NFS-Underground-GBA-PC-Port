"""Real consecutive original scenes: history-only replay must preserve following samples."""
if __name__=='__main__':
 import textwrap,json
 from pathlib import Path
 source=Path('work/camera/test_native_process_transaction_reload.py').read_text()
 prefix=source.split(' workers=[]')[0].split("if __name__=='__main__':",1)[1]
 exec(compile(textwrap.dedent(prefix),'capture-setup','exec'))
 from owned_process_preparation_service import ProcessPreparationService,ProcessSamples
 from test_scene_process_transport import digest
 captures=[]
 def collect(frame,bytes_used=None,scene=None):captures.append((bytes(frame),scene))
 worker=SimpleNamespace(submit=collect);last=0;submitted=0
 try:
  for row in rows:
   if d.nf_native_scene_refresh()>=8749:break
   d.nf_frame(int(row['keys']))
  assert d.nf_world_trace(b'') and d.nf_layer_queue_enable(1) and d.nf_owned_graph_live_enable(1)
  assert d.nf_native_model_plan_trace(b'',model_plan_table,len(model_plan_table))
  for update in range(60):
   d.nf_frame(1);submit_latest()
   if len(captures)>=3:break
  assert len(captures)==3
  import os,time,statistics
  from owned_native_sparse_reader import NativeSparseReader
  from owned_endpoint_road_selection import Reader,endpoint_road_span_candidates
  from owned_closed_scene_memory import scene_memory
  from owned_complete_road_candidates import road_candidates
  import struct
  reciprocal=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072])
  timings=[];exact=0
  for _,scene in captures:
   memory=scene_memory(scene.graph,rom_owned);sources=road_candidates(scene.graph,memory)
   os.environ.pop('NF_NATIVE_ROAD_READER',None)
   expected=endpoint_road_span_candidates(scene.graph,memory,sources,reciprocal,include_empty=True)
   for iteration in range(20):
    begin=time.perf_counter_ns();owner=NativeSparseReader(memory,Reader);setup=time.perf_counter_ns()-begin
    for mode in (iteration%2,1-iteration%2):
     if mode:os.environ['NF_NATIVE_ROAD_READER']='1'
     else:os.environ.pop('NF_NATIVE_ROAD_READER',None)
     begin=time.perf_counter_ns();actual=endpoint_road_span_candidates(scene.graph,memory,sources,reciprocal,include_empty=True);elapsed=time.perf_counter_ns()-begin
     assert actual==expected;exact+=1
     timings.append(dict(refresh=scene.identity[1],native=bool(mode),iteration=iteration,wall_ns=elapsed,reader_setup_ns=setup))
  result=dict(exact_span_comparisons=exact,reader_setup_median_ms=statistics.median(x['reader_setup_ns'] for x in timings)/1e6,modes={str(mode):dict(median_ms=statistics.median(v:=[x['wall_ns']/1e6 for x in timings if x['native']==mode]),max_ms=max(v)) for mode in (False,True)},timings=timings,scope='Fixed original captures, alternating reader modes; complete endpoint span parity. Not live cadence or exclusive scheduling attribution.')
  Path('work/camera/prototype-runs/fixed-native-road-reader.json').write_text(json.dumps(result,indent=2));print({k:v for k,v in result.items() if k!='timings'})
 finally:d.nf_close()
