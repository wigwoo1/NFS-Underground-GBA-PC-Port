from collections import defaultdict,deque
import struct,json
from scene_batches import records
def model_commands(p):
 raw=(p/'motion-live-native-model-plans.bin').read_bytes();offset=0;plans=defaultdict(deque)
 while offset<len(raw):
  magic,refresh,context,ok,count=struct.unpack_from('<5I',raw,offset);offset+=20
  assert magic==0x314d504e and ok and count<=65536
  words=struct.unpack_from('<'+str(count*7)+'I',raw,offset);offset+=count*28
  plans[(refresh,context)].append(words)
 selected={c['event'] for c in json.loads((p/'native-model-joined-writer-calls.json').read_text())};result=[]
 for event in records(p/'motion-original-model-rect-world.bin'):
  if event['pc']!=0x03004770:continue
  key=(event['frame'],event['regs'][4]);assert plans[key]
  words=plans[key].popleft()
  if event['id'] not in selected:continue
  context=event['blocks'][51][1];texture=struct.unpack_from('<I',context,52)[0];shift=struct.unpack_from('<H',context,56)[0]
  for i in range(len(words)//7):
   row=list(words[i*7:i*7+7]);result.append(dict(event=event['id'],polygon=row[0],params=row[1:],texture=texture,shift=shift))
 return result
