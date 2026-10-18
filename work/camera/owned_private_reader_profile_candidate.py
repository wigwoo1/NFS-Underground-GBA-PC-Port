"""Calling-thread native reader stages, attached to captured frame diagnostics."""
import ctypes as C,threading
from pathlib import Path
import _owned_frame_capture_profile_candidate as extension
library=C.CDLL(str(Path('work/camera/viewport-sky-private-stages-probe.dll').resolve()))
library.nf_private_reader_stages.argtypes=[C.c_void_p];library.nf_private_reader_stages.restype=C.c_int
original=extension.capture;local=threading.local()
def capture(address,epoch,refresh):
 packet=original(address,epoch,refresh)
 out=(C.c_uint64*12)();assert library.nf_private_reader_stages(out)==1
 values=list(out);assert values[:2]==[epoch,refresh] and values[9]==len(packet) and values[10:]==[1,160]
 local.values=values
 return packet
def last():return list(local.values)
extension.capture=capture
