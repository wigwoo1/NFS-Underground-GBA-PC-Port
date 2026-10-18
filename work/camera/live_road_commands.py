from collections import defaultdict,deque
import struct
from scene_batches import records
def road_commands(p):
 raw=(p/'motion-live-native-model-plans.bin.road.bin').read_bytes();offset=0;plans=defaultdict(deque)
 while offset<len(raw):
  magic,refresh,context,ok,count,lo,hi=struct.unpack_from('<7I',raw,offset);offset+=28
  assert magic==0x3152504e and ok and count<=8192
  words=struct.unpack_from('<'+str(count*17)+'I',raw,offset);offset+=count*68
  plans[(refresh,context)].append((words,lo|(hi<<32)))
 fields=(0,1,2,5,6,7,8,9,10,11,14,15);result=[];index=0
 for event in records(p/'motion-original-source-8750-8781.bin'):
  if event['pc']!=0x030032f0:continue
  key=(event['frame'],event['regs'][1]);assert plans[key],('missing live road record',key)
  words,missing=plans[key].popleft()
  if index>=2:
   assert not missing
   for i in range(len(words)//17):
    row=list(words[i*17:i*17+17]);r=row[:16];result.append(dict(refresh=event['frame'],event=event['id'],params=r,signature=[r[k] for k in fields]+[row[16]]))
  index+=1
 return result
