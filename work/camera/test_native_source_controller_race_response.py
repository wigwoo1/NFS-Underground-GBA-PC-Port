import ctypes as C,hashlib,time,os
from pathlib import Path
class Pad(C.Structure):_fields_=[('buttons',C.c_uint16),('lt',C.c_uint8),('rt',C.c_uint8),('lx',C.c_int16),('ly',C.c_int16),('rx',C.c_int16),('ry',C.c_int16)]
class State(C.Structure):_fields_=[('packet',C.c_uint32),('pad',Pad)]
root=Path(r'G:\EXTRA DATA DRIVE\Desktop\Games\Codex\NFSUG-Native-PC-Port')
rom=Path(r'G:\EXTRA DATA DRIVE\Desktop\Emulators\GBA\GBA ROMS\Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba')
save=root/'work'/'race.state'
dll=C.CDLL(str(root/'work'/'camera'/'owned-gpu-source-context-free-candidate.dll'))
dll.nf_controller_service_start.argtypes=[C.c_void_p];dll.nf_controller_service_fresh_snapshot.argtypes=[C.c_void_p,C.c_void_p,C.c_uint]
CB=C.WINFUNCTYPE(C.c_uint32,C.c_uint32,C.POINTER(State))
current={'slot':0,'pad':(0,0,0,0,0),'connected':True}
@CB
def poll(slot,target):
 if slot!=current['slot'] or not current['connected']:return 1167
 b,lt,rt,x,y=current['pad'];target.contents.pad=Pad(b,lt,rt,x,y,0,0);return 0
game=C.CDLL(str(root/'work'/'camera'/'viewport-sky-capture-probe.dll'))
game.nf_init.argtypes=[C.c_char_p,C.c_char_p];game.nf_init.restype=C.c_int
game.nf_state.argtypes=[C.c_char_p,C.c_int];game.nf_state.restype=C.c_int
game.nf_frame.argtypes=[C.c_uint];game.nf_read.argtypes=[C.c_uint,C.c_int];game.nf_read.restype=C.c_uint
game.nf_dump.argtypes=[C.c_char_p,C.c_uint,C.c_size_t];game.nf_dump.restype=None
out=(C.c_uint32*2)();serial=C.c_uint64()
def await_state(expected,after):
 deadline=time.monotonic()+3
 while time.monotonic()<deadline:
  assert dll.nf_controller_service_fresh_snapshot(out,C.byref(serial),1000)
  if serial.value>after and list(out)==expected:return
  time.sleep(.001)
 raise AssertionError(('controller snapshot timeout',expected,list(out),serial.value,after))
assert game.nf_init(str(rom).encode(),b'') and game.nf_state(str(save).encode(),0)
assert dll.nf_controller_service_start(poll)
frames=60;cases=[('neutral',(0,0,0,0,0),0),('left_dpad',(4,0,0,0,0),32),('right_dpad',(8,0,0,0,0),16),('neutral_repeat',(0,0,0,0,0),0)]
snapshots={};dump=Path.cwd()/f'.nfsug-race-response-{os.getpid()}.ewram'
try:
 for name,pad,keys in cases:
  if name!='neutral':assert game.nf_state(str(save).encode(),0)
  before=serial.value;current['connected']=True;current['pad']=pad
  assert dll.nf_controller_service_request();await_state([keys,1],before)
  for _ in range(frames):
   game.nf_frame(out[0])
   actual=game.nf_read(0x04000130,2)&1023
   assert actual==((~keys)&1023),(name,keys,actual)
  game.nf_dump(str(dump).encode(),0x02000000,0x40000)
  assert dump.is_file() and dump.stat().st_size==0x40000
  snapshots[name]=dump.read_bytes();dump.unlink()
 neutral=snapshots['neutral'];assert neutral==snapshots['neutral_repeat'],'neutral replay is nondeterministic from same save'
 left=snapshots['left_dpad'];right=snapshots['right_dpad']
 leftdiff=[i for i,(a,b) in enumerate(zip(neutral,left)) if a!=b]
 rightdiff=[i for i,(a,b) in enumerate(zip(neutral,right)) if a!=b]
 assert leftdiff and rightdiff,'steering inputs produced no EWRAM difference after60 frames'
 assert left[0x19d09]!=right[0x19d09] and left[0x19d0a]!=right[0x19d0a],'opposite steering directions did not produce distinct direction-state bytes'
 left_values=[(hex(i),neutral[i],left[i]) for i in leftdiff];right_values=[(hex(i),neutral[i],right[i]) for i in rightdiff]
 print({'result':'PASS_INJECTED_XINPUT_TO_RACE_STATE','frames_per_case':frames,'keys':{'neutral':0,'left':32,'right':16},'neutral_sha256':hashlib.sha256(neutral).hexdigest(),'left_sha256':hashlib.sha256(left).hexdigest(),'right_sha256':hashlib.sha256(right).hexdigest(),'left_diff_bytes':len(leftdiff),'right_diff_bytes':len(rightdiff),'left_deltas':left_values,'right_deltas':right_values,'scope':'Injected XInput callback through native polling service, then actual nf_frame from identical race.state; EWRAM differed under left/right while identical neutral replays matched. Does not test a physical gamepad, window focus, audio, or full 60-fps presentation.'})
finally:
 if dump.exists():dump.unlink()
 assert dll.nf_controller_service_close(3000)
 game.nf_close()