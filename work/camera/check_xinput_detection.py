import ctypes,json
from ctypes import wintypes
class Gamepad(ctypes.Structure):
 _fields_=[('buttons',wintypes.WORD),('left_trigger',ctypes.c_ubyte),('right_trigger',ctypes.c_ubyte),('left_x',ctypes.c_short),('left_y',ctypes.c_short),('right_x',ctypes.c_short),('right_y',ctypes.c_short)]
class State(ctypes.Structure):
 _fields_=[('packet',wintypes.DWORD),('pad',Gamepad)]
dll=ctypes.WinDLL('xinput1_4.dll');fn=dll.XInputGetState;fn.argtypes=[wintypes.DWORD,ctypes.POINTER(State)];fn.restype=wintypes.DWORD
results=[]
for i in range(4):
 s=State();rc=fn(i,ctypes.byref(s));results.append({'slot':i,'result':rc,'connected':rc==0})
print(json.dumps({'scope':'Read-only Windows controller detection; no physical mapping or gameplay proof','slots':results},indent=2))
