from pathlib import Path
p=Path('work/camera');s=(p/'test_source_hud_batches_candidate.py').read_text()
s=s.replace('  assert gpu.nf_source_packets_close()==0;assert gpu.nf_source_packets_begin(1,2,index)==0','''  from owned_source_d3d_consumer_candidate import OwnedD3DConsumer
  import numpy as np
  consumer=OwnedD3DConsumer()
  try: native=consumer.render(gpu)
  finally:consumer.close()
  ref=np.frombuffer(before,np.uint8).reshape(2160,3840,3);packet_checks[-1]['d3d_different_pixels']=int(np.any(native!=ref,axis=2).sum());packet_checks[-1]['d3d_rgb_sha256']=hashlib.sha256(native.tobytes()).hexdigest()
  assert gpu.nf_source_packets_close()==0;assert gpu.nf_source_packets_begin(1,2,index)==0''')
(p/'test_owned_source_d3d_consumer_candidate.py').write_text(s)
