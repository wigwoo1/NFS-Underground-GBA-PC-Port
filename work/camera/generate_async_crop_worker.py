from pathlib import Path
p=Path('work/camera');s=(p/'live_source_batch_candidate.py').read_text()
old=' def _before_gpu_close(self):\n';assert s.count(old)==1
s=s.replace(old,old+"  if hasattr(self,'crop_ledger'):self.crop_ledger.retire();self.async_crop_report=self.crop_ledger.report()\n")
old='LeaseSelect(callback_address(gpu.nf_owned_gpu_target_select))';assert s.count(old)==1
s=s.replace(old,'LeaseSelect(capture_selected)')
marker='   extra=[LeaseAcquire(callback_address(gpu.nf_owned_gpu_target_acquire))';assert s.count(marker)==1
insert="""   from owned_async_crop_ledger import CropLedger
   if not hasattr(self,'crop_ledger'):self.crop_ledger=CropLedger(gpu,limit=getattr(type(self),"async_crop_limit",120))
   selected_position=[0]
   gpu.nf_owned_gpu_target_select.argtypes=[U,U]
   def capture_selected(target,selected_epoch):
    rc=gpu.nf_owned_gpu_target_select(target,selected_epoch)
    if rc:return rc
    position=selected_position[0];selected_position[0]+=1
    if position>=len(metadata):return 37
    try:
     self.crop_ledger.poll()
     if metadata[position]['display_index']>=180:self.crop_ledger.enqueue(metadata[position],target,selected_epoch)
    except Exception as error:
     self.async_crop_error=repr(error);return 37
    return 0
"""
s=s.replace(marker,insert+marker);(p/'live_source_async_crop_candidate.py').write_text(s)
r=(p/'run_queued_source_anchor_candidate.py').read_text().replace("'owned-sky-source-context-candidate.dll'","'owned-async-crop-candidate.dll'");(p/'run_queued_async_crop_candidate.py').write_text(r)

