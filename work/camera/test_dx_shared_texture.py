import ctypes as C,json
from pathlib import Path
p=Path('work/camera').resolve();gpu=C.CDLL(str(p/'owned-sky-gpu.dll'));probe=C.CDLL(str(p/'owned-dx-shared-texture-test.dll'));probe.nf_dx_shared_texture_test.argtypes=[C.c_void_p]
try:
 assert gpu.nf_owned_gpu_window(0)==0
 cycles=[]
 for cycle in range(3):
  out=(C.c_uint64*16)();result=probe.nf_dx_shared_texture_test(out)
  cycles.append(dict(cycle=cycle,result=result,values=list(out)))
  assert result==0 and out[8]+out[9]==1 and out[12]==out[13]==1 and out[14]==0
 evidence=dict(result=result,values=list(out),cycles=cycles,scope='Diagnostic GL-to-D3D11 shared 3840x2160 RGBA texture verification using CPU readback only for test; no swapchain/live presentation claim.')
 Path('work/camera/dx-shared-texture-20261007.json').write_text(json.dumps(evidence,indent=2));print(json.dumps(evidence,indent=2))
 assert result==0 and out[8]+out[9]==1 and out[12]==out[13]==1 and out[14]==0
finally:
 assert gpu.nf_owned_gpu_close() and gpu.nf_owned_gpu_active_contexts()==0
