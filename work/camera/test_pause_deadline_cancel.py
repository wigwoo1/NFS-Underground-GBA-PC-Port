"""Retired presentation waits must cancel even after a complete pause/resume."""
from unittest.mock import patch
from live_owned_gpu_worker import LiveOwnedGPUWorker
w=LiveOwnedGPUWorker.__new__(LiveOwnedGPUWorker)
w.paused=False;w.pause_revision=0
with patch('live_owned_gpu_worker.time.perf_counter_ns',return_value=100):
 assert w.wait_until(100,0)
 w.paused=True
 assert not w.wait_until(1000,0)
 w.paused=False;w.pause_revision=2
 assert not w.wait_until(1000,0)
 assert w.wait_until(100,2)
 w.pause_revision=0
 def transition(_):w.pause_revision=2
 with patch('live_owned_gpu_worker.time.sleep',side_effect=transition) as sleep:
  assert not w.wait_until(1000000000,0)
  assert sleep.call_count==1
  assert sleep.call_args.args[0]<=.01
print('PASS: elapsed, paused, retired-after-resume, fresh and interrupted deadline waits')
