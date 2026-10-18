import runpy
from pathlib import Path
if __name__=='__main__':
 import owned_minimal_queue_timestamps_candidate
 runpy.run_path(str(Path(__file__).with_name('run_native_endpoint_profile_candidate.py')),run_name='__main__')
