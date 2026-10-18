from collections import defaultdict,deque
import struct
from scene_batches import records
def wall_commands(p):
 raw=(p/'motion-live-native-model-plans.bin.wall.bin').read_bytes();offset=0;plans=defaultdict(deque)
 while offset<len(raw):
  magic,refresh,context,ok,count=struct.unpack_from('<5I',raw,offset);offset+=20
  assert magic==0x3157504e and ok and count<=120
  words=struct.unpack_from('<'+str(count*20)+'I',raw,offset);offset+=count*80
  plans[(refresh,context)].append(words)
 result={}
 for event in records(p/'motion-original-source-8750-8781.bin'):
  if event['pc']!=0x03000304:continue
  key=(event['frame'],event['regs'][1]);assert plans[key],('missing live wall plan',key)
  result[event['id']]=plans[key].popleft()
 return result
