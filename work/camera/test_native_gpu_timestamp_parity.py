from pathlib import Path
source=Path('work/camera/test_native_batch_full_motion.py').read_text()
source=source.replace(' assert gpu.nf_owned_gpu_window(0)==0', ' assert gpu.nf_owned_gpu_window(0)==0\n assert gpu.nf_owned_gpu_query_mode(1)==0')
source=source.replace('finally:', " query=(U*104)();assert gpu.nf_owned_gpu_query_read(query)==0 and query[0]==1 and query[2]>=1 and query[6]==0\n checks.append(dict(enabled_timestamp_records=int(query[2]),bounded_pending=int(query[1])))\nfinally:")
source=source.replace('native-batch-full-motion-20261007','native-gpu-timestamp-parity-20261007')
exec(compile(source,'timestamp-parity','exec'))
assert gpu.nf_owned_gpu_query_pending()==0
