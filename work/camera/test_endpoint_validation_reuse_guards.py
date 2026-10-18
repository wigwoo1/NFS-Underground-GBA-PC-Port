import struct,threading,json
from types import SimpleNamespace
from pathlib import Path
import owned_endpoint_validation_reuse_candidate as reuse
camera=bytes(range(48));context=bytes(256)+camera
scene=SimpleNamespace(epoch=1,refresh=10,graph=SimpleNamespace(context=context))
def frame(cam=camera,refresh=10,epoch=1):
 blocks=[b'']*12;blocks[4]=cam
 g=struct.pack('<4I',0x3147534e,1,123,12)+b''.join(struct.pack('<I',len(x))+x for x in blocks)
 return struct.pack('<6I2Q',0x3346474e,refresh,len(g),0,0,0,epoch,refresh*280896)+g
def result(fn,obj,data):
 try:fn(obj,data);return ('ok',)
 except Exception as e:return type(e).__name__,str(e)
reuse.clear();data=frame();assert result(reuse.original,scene,data)==result(reuse.match_frame,scene,data)
assert result(reuse.original,scene,data)==result(reuse.match_frame,scene,data);assert reuse.stats['hits']==1
for obj,raw in [(SimpleNamespace(epoch=2,refresh=10,graph=scene.graph),data),(SimpleNamespace(epoch=1,refresh=11,graph=scene.graph),data),(SimpleNamespace(epoch=1,refresh=10,graph=SimpleNamespace(context=bytes(304))),data),(scene,frame(cam=bytes(48))),(scene,frame(refresh=11)),(scene,b'bad'),(scene,frame()[:-1])]:
 assert result(reuse.original,obj,raw)==result(reuse.match_frame,obj,raw)
mutable=bytearray(data);assert result(reuse.original,scene,mutable)==result(reuse.match_frame,scene,mutable)
mutable[0]=0;assert result(reuse.original,scene,mutable)==result(reuse.match_frame,scene,mutable)
for i in range(5):reuse.summary(frame(refresh=20+i))
assert len(reuse.local.entries)<=2 and sum(len(x[0]) for x in reuse.local.entries)<=reuse.MAX_BYTES
thread_rows=[]
def other():thread_rows.append(len(getattr(reuse.local,'entries',[])));reuse.summary(data);thread_rows.append(len(reuse.local.entries))
t=threading.Thread(target=other);t.start();t.join();assert thread_rows==[0,1]
reuse.install();reuse.uninstall();assert reuse.ClosedGraph.match_frame is reuse.original
out=dict(result='PASS_ENDPOINT_VALIDATION_REUSE_GUARDS',stats=dict(reuse.stats),checks=['identity','changed graph camera on cache hit','changed frame camera','malformed','mutable mutation bypass','bounded eviction','thread isolation','uninstall'])
folder=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/endpoint-validation-reuse-20261010');folder.mkdir(exist_ok=True);(folder/'guards.json').write_text(json.dumps(out,indent=2));print(out)
