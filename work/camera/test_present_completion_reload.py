# Spawn imports this module without initializing a second game host.
if __name__=='__main__':
 """Actual original state reload with complete sky worker retirement/recreation."""
 from multiprocessing.shared_memory import SharedMemory
 from pathlib import Path
 from types import SimpleNamespace
 from live_native_transaction_candidate import NativeTransactionWorker as LiveOwnedGPUWorker
 from owned_sky_capture import SkyCapture
 setup=Path('work/camera/capture_motion_scanline_state.py').read_text().split('gpu=None;gpu_worker=None;gpu_checks=[]')[0].replace('visibility-probe-wide.dll','sky-caller-probe.dll')
 exec(compile(setup,'reload-setup','exec'))
 os.environ['NF_CAPTURE_INDEXED_COPY']='1';assert crt._putenv(b'NF_CAPTURE_INDEXED_COPY=1')==0
 assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(state).encode(),0)
 assert d.nf_native_scene_sink(text_scene_sink,None)
 rom_owned=rom.read_bytes();assert d.nf_live_visibility_enable(rom_owned,len(rom_owned),16*1024*1024)
 assert d.nf_bitmap_text_enable(1)
 for name in ('nf_owned_graph_closed_read','nf_owned_model_builders_closed_read','nf_owned_supplement_closed_read'):
  getattr(d,name).argtypes=[C.c_uint64,C.c_uint,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)]
 d.nf_native_live_latest_frame.restype=C.c_uint
 sky_capture=SkyCapture(d,rom_owned)
 opt=SimpleNamespace(graph_snapshots=True,regenerate_walls=False,diagnostic_wall_frames=0,interpolate_sky=True,attach_sky=False)
 model_scene_dir=None;graph_checks=[];producer_costs=[];live_begin=None;inputs=[];last_scene_step=0;wall_failure=None
 frame=C.create_string_buffer(0x1000000)
 source=Path('work/camera/run_owned_native_prototype.py').read_text()
 body=source[source.index(' def submit_latest():'):source.index(' def controls():')]
 exec(compile('\n'.join(line[1:] for line in body.splitlines()),'production-submit-latest','exec'))
 workers=[];evidence=[];partial=[];old_retained=None
 try:
  for cycle in range(2):
   for row in rows:
    if d.nf_native_scene_refresh()>=8749:break
    d.nf_frame(int(row['keys']))
   assert d.nf_native_scene_refresh()>=8749
   assert d.nf_world_trace(b'') and d.nf_layer_queue_enable(1) and d.nf_owned_graph_live_enable(1)
   assert d.nf_native_model_plan_trace(b'',model_plan_table,len(model_plan_table))
   epoch=d.nf_native_scene_epoch();last=0;submitted=0
   worker=LiveOwnedGPUWorker(epoch,draw_only=True,present=True,paced=True,verify=False,delay_refreshes=12,expected_frames=None,show_window=False,interpolate=True,full_scene_rom=rom_owned,background_prepare=True,precompute_world_samples=True,process_prepare=True,shared_process_output=True,sky_interpolate=True,sky_continuous=True,native_present_callback=True)
   worker.present_completion_barrier=True
   workers.append(worker);worker.start_clock(time.perf_counter_ns(),d.nf_native_scene_refresh())
   if old_retained is not None:
    try:worker.submit(old_retained[0],scene=old_retained[1])
    except ValueError:pass
    else:raise AssertionError('Old epoch accepted by new worker')
   seen=0
   for update in range(60):
    d.nf_frame(1|(32 if update>=20 else 0))
    latest=d.nf_native_live_latest_frame()
    if latest and latest>last:
     # Reload starts inside an original copy: only the known first incomplete
     # publication may be skipped; subsequent publications must be complete.
     ident=(C.c_uint32*3)()
     if cycle and not submitted and not d.nf_live_completed_sky_publication_identity(epoch,latest,ident):
      if not partial:partial.append(dict(epoch=epoch,refresh=latest));last=latest;continue
      raise AssertionError('More than first reload publication lacks sky')
    submit_latest()
   assert submitted>=8 and worker.first_frame_ready.wait(30) and not worker.errors,(cycle,submitted,worker.errors)
   old_retained=worker.preparation_previous
   shared_name=worker.preparation_service.shared_owner.memory.name
   try:worker.close()
   except Exception:
    out=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/present-completion-reload-20261007');out.mkdir(parents=True,exist_ok=True)
    (out/'failure.json').write_text(json.dumps(dict(cycle=cycle,producer=worker.producer,rows=[{k:r.get(k) for k in ('epoch','refresh','consumer_thread','context_count')} for r in worker.results],shutdown=worker.shutdown_evidence),indent=2));raise
   assert not worker.preparation_service.process.is_alive() and worker.preparation_service.connection.closed
   try:
    leaked=SharedMemory(name=shared_name)
   except FileNotFoundError:pass
   else:
    leaked.close();raise AssertionError("Retired preparation shared memory remains accessible")
   assert worker.results and any(row.get('sky_interpolated') and row.get('full_scene_sampled') for row in worker.results),'No fullscene interpolated sky presentation'
   assert all(row['epoch']==epoch for row in worker.results)
   assert all(row.get('native_transaction_candidate') and row.get('present_completion_barrier') for row in worker.results if row.get('interpolated'))
   assert all(row.get('sky_phase_mode')=='continuous_angle' for row in worker.results if row.get('sky_interpolated'))
   assert not worker.shutdown_evidence['gpu_thread_alive'] and worker.shutdown_evidence['native_owner_released'] and not worker.shutdown_evidence['preparation_thread_alive']
   evidence.append(dict(epoch=epoch,scenes=submitted,presentations=len(worker.results),full_scene_sky_samples=sum(bool(row.get('sky_interpolated') and row.get('full_scene_sampled')) for row in worker.results),shutdown=worker.shutdown_evidence,preparation_process_exited=True,pipe_closed=True,shared_memory_released=True))
   if cycle==0:
    assert d.nf_state(str(state).encode(),0)
    assert d.nf_native_scene_epoch()!=epoch and d.nf_native_live_latest_frame()==0
 finally:
  for worker in workers:
   if worker.owner is not None:worker.close()
  d.nf_close()
 for item in (old_retained,):item[1].sky.asset.verify(item[1].sky.boundary)
 out=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/present-completion-reload-20261007');out.mkdir(parents=True,exist_ok=True)
 (out/'tests.json').write_text(json.dumps(dict(result='PASS',cycles=evidence,partial_first_publications=partial,scope='Actual original state reload and complete separate-process scene/sky preparation with bounded shared output/native presentation across clean worker recreation; hidden-window lifecycle, not sustained gameplay/scanout'),indent=2))
 (out/'test_present_completion_reload.py').write_bytes(Path(__file__).read_bytes())
 print('PASS complete sky worker reload',evidence)
