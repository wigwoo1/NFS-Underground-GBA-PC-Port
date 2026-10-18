"""Actual segmented GPU draw/lease/select/present through single queued bridge."""
import sys
from pathlib import Path
source=Path('work/camera/test_segmented_original_gpu_parity.py').read_text()
needle='  assert gpu.nf_owned_gpu_segmented_source_context_callback(C.byref(context))==0'
inject="""  from owned_native_presentation_batch import BatchItem
  from live_native_transaction_candidate import PresentContext
  U=C.c_uint64;P=C.c_void_p;CB=C.CFUNCTYPE(C.c_int,P);AC=C.CFUNCTYPE(C.c_int,C.POINTER(U));SC=C.CFUNCTYPE(C.c_int,U,U);RC=C.CFUNCTYPE(C.c_int,U)
  bridge=C.CDLL(str((p/'owned-batch-queued-single-candidate.dll').resolve()))
  bridge.nf_owned_handoff_create.argtypes=[U];bridge.nf_owned_handoff_create.restype=P;bridge.nf_owned_handoff_destroy.argtypes=[P]
  batch=bridge.nf_owned_handoff_batch_queued;batch.argtypes=[P,U,U,P,C.c_uint,CB,CB,P,P,P,P,AC,SC,RC,RC]
  epoch=scenes[0].graph.epoch;q=bridge.nf_owned_handoff_create(epoch)
  present_context=PresentContext(epoch,0,-999,0);item=BatchItem()
  item.older=scenes[0].graph.refresh;item.newer=scenes[1].graph.refresh;item.index=0;item.deadline=0;item.alpha=alpha;item.drawctx=C.addressof(context);item.presentctx=C.addressof(present_context)
  committed=(U*8)();wait=(U*4)();stage=(U*7)();done=C.c_uint();observed=[]
  actual_present=CB(C.cast(gpu.nf_owned_gpu_present_callback,P).value)
  @CB
  def verify_present(ctx):
   read=gpu.nf_owned_gpu_read(rgb,len(rgb));observed.append(read==0 and rgb.raw==before)
   if not observed[-1]:return 0
   return actual_present(ctx)
  try:
   result=batch(q,epoch,1,C.byref(item),1,CB(C.cast(gpu.nf_owned_gpu_segmented_source_context_callback,P).value),verify_present,committed,wait,stage,C.byref(done),AC(C.cast(gpu.nf_owned_gpu_target_acquire,P).value),SC(C.cast(gpu.nf_owned_gpu_target_select,P).value),RC(C.cast(gpu.nf_owned_gpu_target_release,P).value),RC(C.cast(gpu.nf_owned_gpu_target_ordered,P).value))
   assert result==1 and done.value==1 and observed==[True] and present_context.result==0,(result,done.value,observed,present_context.result)
  finally:bridge.nf_owned_handoff_destroy(q)
"""
assert needle in source
source=source.replace(' for index,item in enumerate(expected):\n  alpha=item[', ' queued_owners=[]\n for index,item in enumerate(expected):\n  alpha=item[')
source=source.replace(needle,inject+'  queued_owners.append(segmented)\n')
source=source.replace("result='PASS_SEGMENTED_COMPLETE_SOURCE_4K_PIXELS'", "result='PASS_SINGLE_QUEUED_GPU_4K_PIXELS'")
source=source.replace(' assert len(set(images))>1'," assert len(queued_owners)==len(expected)\n items=(BatchItem*len(expected))();presents=[];observations=[]\n for i,(owner,item) in enumerate(zip(queued_owners,items)):\n  owner.context.tail_bytes+=1\n  pc=PresentContext(epoch,0,-999,0);presents.append(pc)\n  item.older=scenes[0].graph.refresh;item.newer=scenes[1].graph.refresh;item.index=i;item.deadline=0;item.alpha=expected[i]['alpha'];item.drawctx=C.addressof(owner.context);item.presentctx=C.addressof(pc)\n @CB\n def batch_present(ctx):\n  i=len(observations)\n  if i>=len(references):return 0\n  read=gpu.nf_owned_gpu_read(rgb,len(rgb));exact=read==0 and rgb.raw==references[i]\n  observations.append(exact)\n  if not exact:return 0\n  return actual_present(ctx)\n q=bridge.nf_owned_handoff_create(epoch);done=C.c_uint();committed=(U*(8*len(expected)))();wait=(U*(4*len(expected)))();stage=(U*(7*len(expected)))()\n try:\n  result=batch(q,epoch,1,items,len(expected),CB(C.cast(gpu.nf_owned_gpu_segmented_source_context_callback,P).value),batch_present,committed,wait,stage,C.byref(done),AC(C.cast(gpu.nf_owned_gpu_target_acquire,P).value),SC(C.cast(gpu.nf_owned_gpu_target_select,P).value),RC(C.cast(gpu.nf_owned_gpu_target_release,P).value),RC(C.cast(gpu.nf_owned_gpu_target_ordered,P).value))\n  assert result==1 and done.value==len(expected) and observations==[True]*len(expected)\n  assert list(committed)[4::8]==list(range(len(expected))) and all(x.result==0 for x in presents)\n  print('PASS actual GPU multi-item queued batch',len(expected))\n finally:bridge.nf_owned_handoff_destroy(q)\n"+' assert len(set(images))>1')
source=source.replace("result='PASS_SINGLE_QUEUED_GPU_4K_PIXELS'","result='PASS_MULTI_QUEUED_GPU_4K_PIXELS',queued_batch_count=len(observations),queued_batch_each_rgb_exact=observations,committed_indices=list(committed)[4::8]")
source=source.replace(' assert len(set(images))>1'," bridge.nf_owned_handoff_pause.argtypes=[P,C.c_uint]\n q=bridge.nf_owned_handoff_create(epoch);cancelled_committed=(U*(8*len(expected)))();done=C.c_uint();paused_observations=[];polls=[0]\n @RC\n def pause_ready(token):\n  polls[0]+=1\n  if polls[0]==2:assert bridge.nf_owned_handoff_pause(q,1)==1\n  return gpu.nf_owned_gpu_target_ordered(token)\n @CB\n def paused_present(ctx):\n  i=len(paused_observations);read=gpu.nf_owned_gpu_read(rgb,len(rgb));paused_observations.append(read==0 and rgb.raw==references[i])\n  return actual_present(ctx) if paused_observations[-1] else 0\n gpu.nf_owned_gpu_target_ordered.argtypes=[U]\n try:\n  result=batch(q,epoch,1,items,len(expected),CB(C.cast(gpu.nf_owned_gpu_segmented_source_context_callback,P).value),paused_present,cancelled_committed,wait,stage,C.byref(done),AC(C.cast(gpu.nf_owned_gpu_target_acquire,P).value),SC(C.cast(gpu.nf_owned_gpu_target_select,P).value),RC(C.cast(gpu.nf_owned_gpu_target_release,P).value),pause_ready)\n  assert result==0 and done.value==1 and paused_observations==[True],(result,done.value,paused_observations)\n finally:bridge.nf_owned_handoff_destroy(q)\n print('PASS actual GPU cancellation after one commit')\n"+' assert len(set(images))>1')
source=source.replace(' assert gpu.nf_owned_gpu_close()', ' assert gpu.nf_owned_gpu_close()\n gpu.nf_owned_gpu_pool_stats.argtypes=[P];gpu.nf_owned_gpu_pool_fences.argtypes=[P]\n cleared=(U*5)();fences=(U*4)();assert gpu.nf_owned_gpu_pool_stats(cleared)==0 and list(cleared)==[0]*5\n assert gpu.nf_owned_gpu_pool_fences(fences)==0 and fences[0]==fences[1] and fences[3]==0')
source=source.replace('pixels_per_frame=8294400','pause_prefix_committed=done.value,pause_prefix_rgb_exact=paused_observations,pool_after_close=list(cleared),fences_after_close=list(fences),pixels_per_frame=8294400')
exec(compile(source,'multi_queued_gpu_cleanup_oracle','exec'))

