from pathlib import Path
p=Path('work/camera');source=(p/'live_source_batch_candidate.py').read_text()
needle="   extra=[LeaseAcquire(callback_address(gpu.nf_owned_gpu_target_acquire)),LeaseSelect(callback_address(gpu.nf_owned_gpu_target_select)),LeaseToken(callback_address(gpu.nf_owned_gpu_target_release)),LeaseToken(callback_address(gpu.nf_owned_gpu_target_ordered if ordered_gpu else gpu.nf_owned_gpu_target_ready))]"
assert source.count(needle)==1
hook='''   import hashlib
   if not hasattr(self,'sky_pixel_diagnostics'):self.sky_pixel_diagnostics=[]
   selected_position=[0]
   gpu.nf_owned_gpu_target_select.argtypes=[U,U];gpu.nf_owned_gpu_read.argtypes=[P,C.c_size_t]
   def diagnostic_select(target,selected_epoch):
    rc=gpu.nf_owned_gpu_target_select(target,selected_epoch)
    if rc:return rc
    position=selected_position[0];selected_position[0]+=1
    if position>=len(metadata):return 37
    if len(self.sky_pixel_diagnostics)<60:
     try:
      buffer=C.create_string_buffer(3840*2160*3)
      readrc=gpu.nf_owned_gpu_read(buffer,len(buffer))
      if readrc:return readrc
      # Fixed sky-area crop; foreground may occlude it, so change is not sky-only proof.
      pixels=buffer.raw;crop=b''.join(pixels[(y*3840+300)*3:(y*3840+3540)*3] for y in range(600,800))
      self.sky_pixel_diagnostics.append(dict(metadata[position],token=int(target),selected_epoch=int(selected_epoch),thread=threading.get_ident(),sha256=hashlib.sha256(crop).hexdigest(),fraction=rows[position][-1].weight,readback_bytes=len(buffer),crop=[300,600,3540,800]))
     except Exception as error:
      self.sky_pixel_diagnostics.append(dict(error=repr(error)));return 37
    return 0
   extra=[LeaseAcquire(callback_address(gpu.nf_owned_gpu_target_acquire)),LeaseSelect(diagnostic_select),LeaseToken(callback_address(gpu.nf_owned_gpu_target_release)),LeaseToken(callback_address(gpu.nf_owned_gpu_target_ordered if ordered_gpu else gpu.nf_owned_gpu_target_ready))]'''
(p/'live_source_sky_pixels_candidate.py').write_text(source.replace(needle,hook))
(p/'run_source_sky_pixels_candidate.py').write_text('''"""Isolated selected-target CPU readback diagnostics; never timing certification."""
import sys,runpy,json,time
from pathlib import Path
import live_source_sky_pixels_candidate as diagnostic
sys.modules['live_source_batch_candidate']=diagnostic
original=diagnostic.SourceBatchWorker._after_gpu_close
# Anchor runner assigns cleanup itself; export at process exit from tracked instance.
import atexit
instances=[]
init=diagnostic.SourceBatchWorker.__init__
def tracked(self,*args,**kwargs):
 init(self,*args,**kwargs);instances.append(self)
diagnostic.SourceBatchWorker.__init__=tracked
def export():
 path=Path('work/camera/prototype-runs')/('selected-sky-pixels-'+str(time.time_ns())+'.json')
 path.write_text(json.dumps(dict(scope='Selected queue target before presentation, diagnostic synchronous readback affects cadence. Crop may contain foreground; not physical scanout.',records=[row for obj in instances for row in getattr(obj,'sky_pixel_diagnostics',[])]),indent=2));print(path)
atexit.register(export)
runpy.run_path('work/camera/run_source_compact_diagnostics_candidate.py',run_name='__main__')
''')
