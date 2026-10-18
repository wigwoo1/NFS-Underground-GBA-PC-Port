"""Sustained scripted live endpoint rendering with ordinary-bridge state parity."""
from pathlib import Path
import subprocess,os,re,csv,json,hashlib,ctypes as C,math
p=Path('work/camera').resolve();rom='G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';env=os.environ.copy();env['NF_ENDPOINT_RAM_PREFIX']=str(p/'native-endpoint-route')
r=subprocess.run([str(p/'native-endpoint-preview.exe'),str(p/'visibility-probe-wide.dll'),rom,str(p.parent/'driving.state'),str(p/'native-endpoint-route.csv'),'--native-packets','--scripted-route','--seconds','15','--window-buffer'],env=env,capture_output=True,text=True)
values={k:int(v) for k,v in re.findall(r'([a-z_]+)=(\d+)',r.stdout)}
(p/'native-endpoint-route-output.txt').write_text(r.stdout+r.stderr)
assert r.returncode==0,(r.returncode,r.stdout,r.stderr)
assert values['native_endpoint_packets']>200 and values['native_failed']==0 and values['sink_failures']==0
expected=15*16777216/280896;assert abs(values['simulated']-expected)<=2,(values,expected)
rows=list(csv.DictReader((p/'native-endpoint-route.csv').open()));ready=[x for x in rows if x['ready']=='1'];assert ready and all(float(x['alpha'])==0 for x in ready)
d=C.CDLL(str(p.parent/'nfsprobe.dll'));d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_dump.argtypes=[C.c_char_p,C.c_uint32,C.c_uint32];assert d.nf_init(rom.encode(),b'') and d.nf_state(str(p.parent/'driving.state').encode(),0)
try:
 for frame in range(values['simulated']):d.nf_frame(1|(32 if 180<=frame<500 else 16 if 500<=frame<720 else 0))
 hashes={}
 for name,base,n in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
  path=p/f'native-endpoint-route-reference-{name}.bin';d.nf_dump(str(path).encode(),base,n);actual=(p/f'native-endpoint-route-{name}.bin').read_bytes();assert actual==path.read_bytes(),name;hashes[name]=hashlib.sha256(actual).hexdigest()
finally:d.nf_close()
render_ms=[(int(x['render_end_ns'])-int(x['render_start_ns']))/1e6 for x in ready];render_ms.sort()
pose_fields=['camera_x','camera_y','camera_z','object_x','object_y','object_z','camera_qy','camera_qw','object_qy','object_qw'];poses=[tuple(x[k] for k in pose_fields) for x in ready];pose_changes=sum(a!=b for a,b in zip(poses,poses[1:]))
report=dict(result='PASS',render_ms_p50=render_ms[len(render_ms)//2],render_ms_p95=render_ms[int(len(render_ms)*.95)],render_ms_max=render_ms[-1],endpoint_pose_changes=pose_changes,values=values,expected_original_refreshes=expected,final_ram_matches_ordinary_bridge=True,final_ram_sha256=hashes,ready_frames=len(ready),scope='15second scripted route native retained-pose4K live window rendering and original simulation parity. Endpoint motion, missing sky/HUD/audio; no smooth60fps/native-gameplay claim.')
(p/'native-endpoint-route-tests.json').write_text(json.dumps(report,indent=2));print(report)
