"""Spawned geometry envelope round-trip; no live renderer qualification."""
import multiprocessing as mp,struct,json,sys
from pathlib import Path
from owned_geometry_tail_capability_candidate import GeometryTailOwners
from owned_geometry_process_codec_candidate import GeometryFrameDecoder

def child(connection):
 try:
  while True:
   request=connection.recv()
   if request is None:break
   generation,frames=request
   result=[]
   for key,frame in enumerate(frames):
    header=struct.unpack_from('<6I2Q',frame)
    assert header[3:6]==(0,0,0) and len(frame)==40+header[2]
    result.append(('segmented',generation,key,frame,40+header[2],None))
   connection.send(tuple(result))
 finally:connection.close()

if __name__=='__main__':
 folder=Path(sys.argv[1]);owners=tuple((folder/(name+'.frame.bin')).read_bytes() for name in ('older','newer'))
 context=mp.get_context('spawn');parent,remote=context.Pipe();process=context.Process(target=child,args=(remote,));process.start();remote.close()
 restored=[];rejections=0
 try:
  for generation in (0,1,2):
   capability=GeometryTailOwners(generation,owners);decoder=GeometryFrameDecoder(generation,owners)
   parent.send((generation,tuple(capability.geometry(generation,k) for k in range(2))))
   assert parent.poll(15),'Child response timeout'
   wires=parent.recv()
   for key,wire in enumerate(wires):
    frame=decoder.decode(wire);assert bytes(frame)==owners[key];restored.append(frame)
   decoder.close();capability.close()
   try:decoder.decode(wires[0])
   except ValueError:rejections+=1
   else:raise AssertionError('Retired generation accepted')
  parent.send(None);process.join(15);assert not process.is_alive() and process.exitcode==0
  assert all(bytes(frame)==owners[index%2] for index,frame in enumerate(restored))
 finally:
  parent.close()
  if process.is_alive():process.terminate();process.join(5)
 result=dict(result='PASS_SPAWNED_GEOMETRY_ENVELOPE_ROUND_TRIP',exact_frames=len(restored),retired_generations_rejected=rejections,child_exitcode=process.exitcode,scope='Real Windows spawned process with private geometry envelopes and exact parent tail restoration over three generations; not full progressive service, shared-memory protocol, renderer or live cadence qualification.')
 Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print(result)
