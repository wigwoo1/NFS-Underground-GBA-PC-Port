import owned_motion_pairs as original
from owned_motion_pairs_bytes_candidate import _decode_records
original._decode_records=_decode_records
import runpy
runpy.run_path('work/camera/test_segmented_original_gpu_parity.py',run_name='__main__')
