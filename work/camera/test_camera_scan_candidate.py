import json,struct,time,statistics
from pathlib import Path
from owned_closed_graph import ClosedGraph as Original
from owned_closed_camera_scan_candidate import ClosedGraph as Candidate
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791417692469356500.json').read_text());folder=Path(r['live_preparation_profiles'][0]['capture'])
from owned_graph_packet import GraphPacket
checks=[];times={'original':[],'candidate':[]}
for name in ('older','newer'):
 supp=(folder/(name+'.supplements.bin')).read_bytes();epoch=struct.unpack_from('<Q',supp,24)[0];refresh=struct.unpack_from('<I',supp,8)[0]
 args=(epoch,refresh,GraphPacket.decode((folder/(name+'.graph.bin')).read_bytes()),*((folder/(name+'.'+x+'.bin')).read_bytes() for x in ('objects','callbacks','associations')))
 a=Original(*args);b=Candidate(*args);frame=(folder/(name+'.frame.bin')).read_bytes();a.match_frame(frame);b.match_frame(frame)
 bad=bytearray(frame);struct.pack_into('<Q',bad,24,epoch+1)
 badkind=bytearray(frame);struct.pack_into('<I',badkind,44,99)
 badlen=bytearray(frame);struct.pack_into('<I',badlen,56,0x100001)
 for f in (bad,badkind,badlen,frame[:39]):
  outcomes=[]
  for c in (a,b):
   try:c.match_frame(f)
   except ValueError as e:outcomes.append(str(e))
   else:raise AssertionError('Invalid frame accepted')
  assert outcomes[0]==outcomes[1]
 for n in range(12):
  for label,c in ([('original',a),('candidate',b)] if n%2==0 else [('candidate',b),('original',a)]):
   start=time.perf_counter_ns()
   for _ in range(200):c.match_frame(frame)
   if n>=2:times[label].append((time.perf_counter_ns()-start)/200/1e6)
 checks.append(dict(name=name,epoch=epoch,refresh=refresh,bytes=len(frame),invalid_cases=4))
result=dict(result='PASS_CAMERA_SCAN_COMPONENT',checks=checks,median_match_ms={k:statistics.median(v) for k,v in times.items()},scope='Two captured fullscene frames; complete scanner outcomes and four invalid mutations match original. Component timing only; no live/full4K or physical cadence proof.')
Path('work/camera/camera-scan-component.json').write_text(json.dumps(result,indent=2));print(result)
