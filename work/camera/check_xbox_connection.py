import ctypes as C,json,time
from pathlib import Path
class Pad(C.Structure):
 _fields_=[('buttons',C.c_uint16),('lt',C.c_uint8),('rt',C.c_uint8),('lx',C.c_int16),('ly',C.c_int16),('rx',C.c_int16),('ry',C.c_int16)]
class State(C.Structure):_fields_=[('packet',C.c_uint32),('pad',Pad)]
d=C.WinDLL('xinput1_4');d.XInputGetState.argtypes=[C.c_uint32,C.POINTER(State)];d.XInputGetState.restype=C.c_uint32
slots=[]
for i in range(4):
 s=State();result=d.XInputGetState(i,C.byref(s));slots.append(dict(slot=i,result=result,connected=result==0,packet=s.packet if result==0 else None,buttons=s.pad.buttons if result==0 else None))
out=dict(checked_unix_ns=time.time_ns(),slots=slots,scope='Actual XInput connection inventory only; no physical mapping or gameplay verification.')
Path('work/camera/prototype-runs/xbox-connection-check.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
