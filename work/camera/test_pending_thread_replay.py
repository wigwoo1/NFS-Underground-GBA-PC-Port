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
  from owned_world_preparation_service import WorldPreparationService
  from test_scene_process_transport import digest
  def run(first_alphas,next_alphas):
   service=WorldPreparationService(rom_owned,2)
   try:
    service.warm_start(*captures[0])
    first=service.take(service.submit(captures[0],captures[1],first_alphas,timeout=30))
    try:
     assert getattr(first,'history_only',False)==(not first_alphas)
     if not first_alphas:
      try:first.sample(0)
      except ValueError:pass
      else:raise AssertionError('History-only sample accepted')
    finally:first.close()
    following=service.take(service.submit(captures[1],captures[2],next_alphas,timeout=30))
    try:return {a:digest(following.sample(a)) for a in next_alphas}
    finally:following.close()
   finally:service.close()
  baseline=run((0,.5,1),(0,.5,1))
  assert run((),(0,.5,1))==baseline
  partial=run((.5,1),(.5,1));assert partial=={a:baseline[a] for a in (.5,1)}
  Path('work/camera/prototype-runs/thread-pending-replay-parity.json').write_text(json.dumps(dict(captured_refreshes=[s.identity[1] for _,s in captures],following_full_samples_exact=3,following_partial_samples_exact=2,history_only_sampling_rejected=True,services_closed=3),indent=2))
  print('PASS actual thread history-only and partial replay following samples')
 finally:d.nf_close()
