import sys,json,ctypes as C,struct,hashlib,threading
from pathlib import Path
sys.argv=['test','work/camera/prototype-runs/owned-native-1791434872973979000.json']
setup=Path('work/camera/test_owned_native_source_backdrop_batch_parity_candidate.py').read_text().split('session=None;results=[]')[0]
exec(compile(setup,'actual_capture_setup','exec'))
from owned_source_d3d_sky_pan_candidate import OwnedD3DConsumer
from owned_source_segmented_draw_candidate import OwnedSourceDraw as SegmentedDraw
from owned_prepared_world_segmented_candidate import PreparedWorldMotion
from owned_segmented_frame_candidate import SegmentedFrame
import owned_endpoint_road_planner as planner_module
from owned_endpoint_road_selection_reuse_candidate import endpoint_road_span_candidates
planner_module.endpoint_road_span_candidates=endpoint_road_span_candidates
from owned_sample_types_install_candidate import install
install()
consumer=OwnedD3DConsumer();consumer.bind_window()
s=C.CDLL(str(Path('work/camera/owned-gpu-source-segmented-candidate.dll').resolve()));P=C.c_void_p
s.nf_source_initialize.argtypes=[P];s.nf_source_packets_begin.argtypes=[C.c_uint64]*3;s.nf_source_packets_publish.argtypes=[P];s.nf_owned_gpu_source_context_callback.argtypes=[P];s.nf_owned_gpu_source_segmented_callback.argtypes=[P,C.c_size_t,P,C.c_size_t]
assert s.nf_source_initialize(consumer.window)==0
results=[];cached=None
try:
 prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom);cached=PrecomputedSourceWorldSamples(prepared,tuple(x['alpha'] for x in expected))
 boundaries=[]
 for scene in scenes:
  record=next(x for x in report['sky_capture_records'] if (x['epoch'],x['publication'])==scene.identity);origin=record['asset_origin'];offset=record['source']-0x08000000
  boundaries.append(SkyBoundary(record['epoch'],record['publication'],record['angle'],240,64,0,record['source'],origin,0x06002940,rom[offset:offset+15136]))
 origin=boundaries[0].asset_origin;asset=SkyAsset(origin,rom[origin-0x08000000:origin-0x08000000+15376])
 for index,item in enumerate(expected):
  alpha=item['alpha'];frame,camera,models,bounds,detail=cached.sample(alpha);offsets,mask,total,_=cached.source_masks[alpha]
  original_segment=frame;assert isinstance(original_segment,SegmentedFrame);frame=bytes(frame)
  owned=OwnedSourceDraw(frame,camera,models,bounds,detail['geometry_records'],*cached.source_cameras,alpha,offsets,mask,total).attach_sky(asset.sample_continuous(*boundaries,alpha))
  hashes=[];prefix_size=40+struct.unpack_from('<I',frame,8)[0];prefix=frame[:prefix_size];tail=frame[prefix_size:];prefix_owner=C.c_char_p(prefix);tail_owner=C.c_char_p(tail);original=owned.context.draw.frame
  segframe=original_segment
  materialize=SegmentedFrame.materialize
  def reject_materialization(self):raise AssertionError('Adapter materialized retained tail')
  SegmentedFrame.materialize=reject_materialization
  segowned=SegmentedDraw(segframe,camera,models,bounds,detail['geometry_records'],*cached.source_cameras,alpha,offsets,mask,total).attach_sky(asset.sample_continuous(*boundaries,alpha))
  SegmentedFrame.materialize=materialize
  del segframe
  assert segowned.frame.base is original_segment.base and segowned.tail_pointer==C.cast(segowned.base_owner,P).value+original_segment.tail_offset
  tail_owner=P(segowned.tail_pointer)
  for mode in ('contiguous','segmented'):
   assert s.nf_source_packets_begin(1,1,index)==0
   try:
    if mode=='contiguous':assert s.nf_owned_gpu_source_context_callback(C.byref(owned.context))==0
    else:
     owned=segowned;owned.context.draw.frame=C.cast(prefix_owner,P).value
     for bad_prefix,bad_tail in ((prefix_size-1,len(tail)),(prefix_size,len(tail)-1),(0,len(tail))):assert s.nf_owned_gpu_source_segmented_callback(C.byref(owned.context),bad_prefix,tail_owner,bad_tail)==37
     assert s.nf_owned_gpu_source_segmented_callback(C.byref(owned.context),prefix_size,None,len(tail))==37
     bad_prefix=bytearray(prefix);struct.pack_into('<Q',bad_prefix,24,0);bad_owner=C.c_char_p(bytes(bad_prefix));owned.context.draw.frame=C.cast(bad_owner,P).value
     assert s.nf_owned_gpu_source_segmented_callback(C.byref(owned.context),prefix_size,tail_owner,len(tail))==28
     owned=segowned;owned.context.draw.frame=C.cast(prefix_owner,P).value
     foreign=[];thread=threading.Thread(target=lambda:foreign.append(s.nf_owned_gpu_source_segmented_callback(C.byref(owned.context),prefix_size,tail_owner,len(tail))));thread.start();thread.join();assert foreign==[31]
     assert s.nf_owned_gpu_source_segmented_callback(C.byref(owned.context),prefix_size,tail_owner,len(tail))==0
    publication=(C.c_uint64*7)();assert s.nf_source_packets_publish(publication)==0
    image=consumer.render(s,readback=True);hashes.append(hashlib.sha256(image.tobytes()).hexdigest())
   finally:assert s.nf_source_packets_close()==0;owned.context.draw.frame=original
  assert hashes[0]==hashes[1]
  saved=json.loads(Path('work/camera/prototype-runs/source-segmented-parity-20261008.json').read_text())['samples']
  assert hashes[0]==saved[index]['rgb_sha256']
  results.append(dict(alpha=alpha,rgb_sha256=hashes[0],prefix_bytes=prefix_size,tail_bytes=len(tail)))
finally:
 assert s.nf_owned_gpu_close()==1;consumer.close()
 if cached is not None:cached.close()
 history.close()
out=dict(result='PASS_SAMPLE_TYPES_SOURCE_4K_PARITY',samples=results,invalid_lengths_rejected=True,foreign_thread_rejected=True,scope='Actual captured source callback and ten 4K GPU readbacks; harness slices copied tail for test only. End-to-end no-copy/live path pending.')
Path('work/camera/prototype-runs/sample-types-4k-parity-20261008.json').write_text(json.dumps(out,indent=2));print(out['result'])






