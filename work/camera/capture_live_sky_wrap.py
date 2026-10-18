"""Bounded diagnostic owned full-scene draw inputs and 4K GPU readback."""
import ctypes as C,json,time
from pathlib import Path
def capture(gpu,frame,camera,models,bounds,sample,older,newer,alpha,index):
 folder=Path('work/camera/prototype-runs')/f'live-sky-wrap-{time.time_ns()}-{index}';folder.mkdir()
 (folder/'frame.bin').write_bytes(frame)
 for name,value in (('camera',camera),('models',models),('bounds',bounds)):
  if value is not None:(folder/(name+'.bin')).write_bytes(C.string_at(C.addressof(value),C.sizeof(value)))
 (folder/'lower.bin').write_bytes(sample.lower);(folder/'upper.bin').write_bytes(sample.upper)
 (folder/'older-sky.bin').write_bytes(older.boundary.encode());(folder/'newer-sky.bin').write_bytes(newer.boundary.encode())
 rgb=C.create_string_buffer(3840*2160*3);assert gpu.nf_owned_gpu_read(rgb,len(rgb))==0;(folder/'rgb.bin').write_bytes(rgb.raw)
 meta=dict(folder=str(folder.resolve()),alpha=alpha,weight=sample.weight,older_serial=older.serial,newer_serial=newer.serial,scope='Full live scene GPU draw readback; capture perturbs timing, no cadence claim')
 (folder/'capture.json').write_text(json.dumps(meta,indent=2));return meta
