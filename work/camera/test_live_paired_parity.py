from pathlib import Path
import subprocess,os,re,ctypes as C,hashlib,json,csv,statistics,sys
p=Path('work/camera').resolve();root=p.parent
rom='G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba'
duration=int(sys.argv[1]) if len(sys.argv)>1 else 15
window='--window-buffer' in sys.argv[2:]
env=dict(os.environ,NF_ENDPOINT_RAM_PREFIX=str(p/'live-paired-parity'))
log=subprocess.check_output([str(p/'native-endpoint-preview.exe'),str(p/'visibility-probe-wide.dll'),rom,str(root/'driving.state'),str(p/'live-paired-parity.csv'),'--paired-packets','--scripted-route','--seconds',str(duration),'--delay-refreshes','8']+(['--window-buffer'] if window else []),env=env,text=True)
assert int(re.search(r'rejected_scenes=(\d+)',log)[1])==0,log
assert int(re.search(r'paired_rejected=(\d+)',log)[1])==0,log
(p/'live-paired-parity.log').write_text(log);n=int(re.search(r'simulated=(\d+)',log)[1])
d=C.CDLL(str(root/'nfsprobe.dll'));d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_dump.argtypes=[C.c_char_p,C.c_uint32,C.c_uint32]
assert d.nf_init(rom.encode(),b'') and d.nf_state(str(root/'driving.state').encode(),0)
try:
 for i in range(n):d.nf_frame(1|(32 if 180<=i<500 else 16 if 500<=i<720 else 0))
 hashes={}
 for name,base,size in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
  path=p/f'live-paired-baseline-{name}.bin';d.nf_dump(str(path).encode(),base,size)
  baseline=path.read_bytes();actual=(p/f'live-paired-parity-{name}.bin').read_bytes();assert baseline==actual,name
  hashes[name]=hashlib.sha256(actual).hexdigest()
finally:d.nf_close()
rows=list(csv.DictReader(open(p/'live-paired-parity.csv')));ready=[r for r in rows if int(r['ready'])]
def stats(values):return dict(median=statistics.median(values),p95=sorted(values)[int(.95*len(values))],maximum=max(values),over_16_667ms=sum(v>1000/60 for v in values))
sim=[(int(r['simulation_end_ns'])-int(r['simulation_start_ns']))/1e6 for r in rows]
combined=[(int(r['render_end_ns'])-int(r['simulation_start_ns']))/1e6 for r in ready]
poses=[tuple(r[k] for k in ('camera_x','camera_y','camera_z','object_x','object_y','object_z','camera_qx','camera_qy','camera_qz','camera_qw','object_qx','object_qy','object_qz','object_qw')) for r in ready]
swap_ms=[(int(r['swap_end_ns'])-int(r['render_end_ns']))/1e6 for r in rows]
intervals=[(int(b['swap_end_ns'])-int(a['swap_end_ns']))/1e6 for a,b in zip(rows,rows[1:])]
components={name:stats([int(r[name])/1e6 for r in ready]) for name in ('endpoint_prepare_ns','paired_prepare_ns')}
report=dict(pose_changes=sum(a!=b for a,b in zip(poses,poses[1:])),nonzero_alpha=sum(float(r["alpha"])>0 for r in ready),window_stage_swap_ms=stats(swap_ms),swap_interval_ms=stats(intervals),duration_seconds=duration,window_buffer=window,component_ms=components,result='PASS',scope='Exact final EWRAM/IWRAM at identical scripted input and refresh count; diagnostic offscreen timing, no smooth60fps claim',refreshes=n,ram_hashes=hashes,simulation_batch_ms=stats(sim),simulation_plus_generation_render_ms=stats(combined),host_output=log)
(p/'live-paired-parity-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
