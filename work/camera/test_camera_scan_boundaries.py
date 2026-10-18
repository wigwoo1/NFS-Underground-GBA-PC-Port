import json,struct
from pathlib import Path
from owned_closed_graph import ClosedGraph as Original
from owned_closed_camera_scan_candidate import ClosedGraph as Candidate
from owned_graph_packet import GraphPacket
from owned_segmented_frame_candidate import SegmentedFrame
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791417692469356500.json').read_text());folder=Path(r['live_preparation_profiles'][0]['capture']);checks=[]
for name in ('older','newer'):
 supp=(folder/(name+'.supplements.bin')).read_bytes();epoch=struct.unpack_from('<Q',supp,24)[0];refresh=struct.unpack_from('<I',supp,8)[0]
 args=(epoch,refresh,GraphPacket.decode((folder/(name+'.graph.bin')).read_bytes()),*((folder/(name+'.'+x+'.bin')).read_bytes() for x in ('objects','callbacks','associations')))
 a=Original(*args);b=Candidate(*args);frame=(folder/(name+'.frame.bin')).read_bytes();gn=struct.unpack_from('<I',frame,8)[0];end=40+gn;at=40;camera_offsets=[];kind_offsets=[];lengths=[]
 while at<end:
  kind=struct.unpack_from('<I',frame,at+4)[0];kind_offsets.append(at+4);at+=16
  for i in range(12):
   lengths.append(at);n=struct.unpack_from('<I',frame,at)[0];at+=4
   if kind in (1,2) and i==(4 if kind==1 else 3):camera_offsets.append(at)
   at+=n
 assert at==end and camera_offsets
 variants={'valid':frame}
 camera=bytearray(frame);camera[camera_offsets[-1]]^=1;variants['camera_mismatch']=bytes(camera)
 no_world=bytearray(frame)
 for pos in kind_offsets:struct.pack_into('<I',no_world,pos,3)
 variants['no_world_camera']=bytes(no_world)
 late=bytearray(frame);struct.pack_into('<I',late,lengths[-1],0x100001);variants['late_block']=bytes(late)
 both=bytearray(camera);struct.pack_into('<I',both,lengths[-1],0x100001);variants['camera_and_late_block']=bytes(both)
 for mutation,data in variants.items():
  for form,value in [('bytes',data),('mutable',bytearray(data)),('segmented',SegmentedFrame(data[:end],frame,end))]:
   outcomes=[]
   for cls in (a,b):
    try:cls.match_frame(value);outcomes.append('accepted')
    except ValueError as e:outcomes.append(str(e))
   assert outcomes[0]==outcomes[1],(mutation,form,outcomes)
   assert (outcomes[0]=='accepted')==(mutation=='valid')
   checks.append(dict(frame=name,mutation=mutation,form=form,outcome=outcomes[0]))
Path('work/camera/camera-scan-boundaries.json').write_text(json.dumps(dict(result='PASS',checks=checks,scope='Two captured scenes, bytes/mutable/segmented forms, complete validation ordering including late errors. Not fullscene GPU or live timing certification.'),indent=2));print('PASS',len(checks),'camera scanner outcomes')
