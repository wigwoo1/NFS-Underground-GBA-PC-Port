from pathlib import Path
import struct,json
out=[]
for f in [1,2,4,8]:
 iw=Path(f'work/v2/speed-{f}-iwram.bin').read_bytes();ew=Path(f'work/v2/speed-{f}-ewram.bin').read_bytes()
 def u(a):
  b,base=(iw,0x3000000) if a>=0x3000000 else (ew,0x2000000)
  return struct.unpack_from('<I',b,a-base)[0]
 ptr=u(0x30000fc);idx=u(0x3000068);car=ptr+idx*0xa4
 out.append({'cpu_factor':f,'vehicle_array':hex(ptr),'player_index':idx,'vehicle_address':hex(car),'estimated_fps_global':u(0x3005d88),'timer_count':u(0x3006044),'vehicle_x_raw':u(car+12),'vehicle_z_raw':u(car+20),'vehicle_speed_raw':u(car+44)})
Path('outputs/nfsug-native-renderer/physics-observations.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
