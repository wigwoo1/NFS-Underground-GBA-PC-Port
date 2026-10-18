from live_owned_gpu_worker import LiveOwnedGPUWorker
class Resource:
 def __init__(self):self.closed=0;self.refresh=99
 def close(self):self.closed+=1
worker=object.__new__(LiveOwnedGPUWorker);pair=Resource();history=Resource();worker.world_pair=pair;worker.world_history=history;worker.world_roads=('owned',);worker.world_generation=1;worker.world_resets=[]
worker.reset_world_history('generation_changed',3)
assert pair.closed==history.closed==1 and worker.world_pair is worker.world_history is worker.world_roads is None
assert worker.world_generation==3 and worker.world_resets==[dict(reason='generation_changed',refresh=99,generation=1,next_generation=3)]
worker.reset_world_history('worker_shutdown');assert pair.closed==history.closed==1 and len(worker.world_resets)==1
print('PASS full-scene history reset closes owned interval/scratch once and clears retained roads')
