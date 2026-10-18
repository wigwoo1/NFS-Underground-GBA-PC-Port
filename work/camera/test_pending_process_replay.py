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
  from owned_native_sparse_reader import NativeSparseReader
  from owned_endpoint_road_selection import Reader
  from owned_closed_scene_memory import scene_memory
  native_reads=0
  for frame,scene in captures:
   memory=scene_memory(scene.graph,rom_owned);reader=NativeSparseReader(memory,Reader)
   for address,data in memory._ranges:
    for offset,size in ((0,len(data)),(0,min(16,len(data))),(max(0,len(data)-16),min(16,len(data)))):
     output=C.create_string_buffer(size)
     assert reader.callback(reader.pointer,address+offset,output,size) and output.raw==memory.read(address+offset,size)
     native_reads+=1
  from owned_external_model_owners import external_model_owners
  from owned_motion_pairs import records
  for frame,scene in captures:
   expected=external_model_owners(scene.graph,scene.builders,frame,rom_owned)
   assert external_model_owners(scene.graph,scene.builders,frame,rom_owned,decoded_rows=records(frame)['records'])==expected

  def run(first_alphas,next_alphas):
   service=ProcessPreparationService(rom_owned,2,shared_output=True)
   name=service.shared_owner.memory.name
   try:
    service.warm_start(*captures[0])
    first=service.take(service.submit(captures[0],captures[1],first_alphas,timeout=30))
    try:
     assert first.history_only==(not first_alphas)
     if not first_alphas:
      try:first.sample(0)
      except ValueError:pass
      else:raise AssertionError('History-only sample accepted')
    finally:first.close()
    following=service.take(service.submit(captures[1],captures[2],next_alphas,timeout=30))
    try:return {a:digest(following.sample(a)) for a in next_alphas}
    finally:following.close()
   finally:
    service.close();assert not service.process.is_alive() and service.connection.closed
    try:memory=SharedMemory(name=name)
    except FileNotFoundError:pass
    else:memory.close();raise AssertionError('Shared output survived close')
  import os
  os.environ.pop('NF_NATIVE_ROAD_READER',None)
  baseline=run((0,.5,1),(0,.5,1))
  import os
  os.environ['NF_NATIVE_ROAD_READER']='1'
  assert run((0,.5,1),(0,.5,1))==baseline

  assert run((),(0,.5,1))==baseline
  assert run((),(.5,1))=={a:baseline[a] for a in (.5,1)}
  valid=dict(history_only=True,tails=[],samples=[],original_bytes=0,transferred_bytes=0)
  rejected=0
  for key,value in [('history_only',1),('tails',[b'bad']),('samples',[(0,None)]),('original_bytes',1),('transferred_bytes',1),('extra',True)]:
   malformed=dict(valid);malformed[key]=value
   try:ProcessSamples(malformed)
   except ValueError:rejected+=1
   else:raise AssertionError('Malformed history-only payload accepted')
  result=dict(consecutive_scenes=[s.identity for _,s in captures],following_exact_samples=3,partial_exact_samples=2,malformed_rejected=rejected,native_reader_exact_reads=native_reads,native_reader_exact_samples=3,closed_services=4,scope='Original complete scenes and child road-history preservation; not a gameplay cadence proof')
  Path('work/camera/prototype-runs/pending-process-replay.json').write_text(json.dumps(result,indent=2));print(result)
 finally:d.nf_close()
