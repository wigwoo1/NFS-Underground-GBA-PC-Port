import ctypes as C,threading,json
from pathlib import Path
p=Path('work/camera');d=C.CDLL(str((p/'owned-gpu-source-packet-identity-candidate.dll').resolve()));d.nf_source_packets_begin.argtypes=[C.c_uint64]*3;d.nf_source_packets_identity.argtypes=[C.c_void_p]
assert d.nf_source_packets_begin(0,1,0)==1;assert d.nf_source_packets_begin(1,0,0)==1
assert d.nf_source_packets_begin(9,7,123)==0;assert d.nf_source_packets_reset()==1
ids=(C.c_uint64*3)();assert d.nf_source_packets_identity(ids)==0 and list(ids)==[9,7,123]
foreign=[]
def worker():foreign.extend([d.nf_source_packets_close(),d.nf_source_packets_identity(ids)])
t=threading.Thread(target=worker);t.start();t.join();assert foreign==[1,1]
assert d.nf_source_packets_close()==0 and d.nf_source_packets_identity(ids)==1
rebind=[]
def next_owner():rebind.extend([d.nf_source_packets_begin(10,8,0),d.nf_source_packets_close()])
t=threading.Thread(target=next_owner);t.start();t.join();assert rebind==[0,0]
r=dict(result='PASS_SOURCE_PACKET_IDENTITY_LIFECYCLE',closed_identity_rejected=True,foreign_close_rejected=True,active_reset_rejected=True,new_owner_after_close=True,scope='Component lifecycle only.')
(p/'prototype-runs/source-packet-identity-lifecycle.json').write_text(json.dumps(r,indent=2));print(r)
