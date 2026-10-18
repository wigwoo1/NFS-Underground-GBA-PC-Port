"""Full-scene asynchronous crop parity using the captured original GPU oracle."""
import sys,json
from pathlib import Path
source=Path('work/camera/test_segmented_original_gpu_parity.py').read_text()
old="baseline_gpu=C.CDLL(str((p/'owned-sky-hud-view-candidate.dll').resolve()))"
assert source.count(old)==1
source=source.replace(old,"baseline_gpu=C.CDLL(str((p/'owned-async-crop-candidate.dll').resolve()))\n baseline_gpu.nf_crop_enqueue.argtypes=[C.c_uint64,C.c_uint,C.c_uint]\n baseline_gpu.nf_crop_poll.argtypes=[C.POINTER(C.c_uint64),C.c_void_p,C.c_size_t]\n crop_checks=[]")
old="   assert baseline_gpu.nf_owned_gpu_read(rgb,len(rgb))==0;references.append(rgb.raw)"
assert source.count(old)==1
source=source.replace(old,"""   assert baseline_gpu.nf_crop_enqueue(index+1,300,600)==0
   assert baseline_gpu.nf_owned_gpu_read(rgb,len(rgb))==0;references.append(rgb.raw)
   small=C.create_string_buffer(3072);sample_id=C.c_uint64();deadline=time.perf_counter()+5;polls=0
   while True:
    rc=baseline_gpu.nf_crop_poll(C.byref(sample_id),small,3072);polls+=1
    if rc:break
    assert time.perf_counter()<deadline;time.sleep(.001)
   oracle=b''.join(rgb.raw[(y*3840+300)*3:(y*3840+364)*3] for y in range(600,616))
   assert rc==1 and sample_id.value==index+1 and small.raw==oracle,'Async crop differs from complete frame'
   crop_checks.append(dict(alpha=alpha,sample_id=sample_id.value,sha256=hashlib.sha256(oracle).hexdigest(),polls=polls))""")
source += "\nresult['async_crop_checks']=crop_checks\nresult['async_crop_bytes']=3072\nPath(sys.argv[2]).write_text(json.dumps(result,indent=2))\n"
exec(compile(source,'async_crop_fullscene_parity','exec'))
