from pathlib import Path
import struct,json
p=Path('work/camera');packet=(p/'road-camera-command-produced.packet').read_bytes();o,n=struct.unpack_from('<2I',packet,48);w=packet[o:o+n];count=struct.unpack_from('<I',w,4)[0];at=8
for i in range(count):
 c,x,y=struct.unpack_from('<3I',w,at);at+=12+c*40+x*y*4
at+=8;rows=[]
for i in range(count):
 mode,size=struct.unpack_from('<2I',w,at);at+=8
 if mode in (9,10):rows.append(dict(surface=i,mode=mode,header=list(struct.unpack_from('<6I',w,at+size-288))))
 at+=size
report=dict(result='GPU_REPLAY_REJECTED',exit_code=42,source_road_rings=0,renderer='AMD Radeon RX 7900 XTX',road_records=rows,scope='Context created and endpoint packet reached draw path; rejected before first source road completed. Affine unsupported source-ring condition present in packet; precise failure branch needs instrumentation.')
(p/'source-road-gpu-replay-tests.json').write_text(json.dumps(report,indent=2));print(report)
