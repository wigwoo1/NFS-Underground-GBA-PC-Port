from pathlib import Path
p=Path('work/camera/test_texture_provenance.py');s=p.read_text().replace('scene_palette_bytes={}','scene_palette_bytes={};kept_candidate=None')
s=s.replace('d.nf_surface_free.argtypes=[C.c_void_p]', 'd.nf_surface_free.argtypes=[C.c_void_p]\nd.nf_live_completed_wall_candidate.argtypes=[C.c_uint64]+[C.c_uint32]*5+[C.c_void_p,C.c_void_p]')
s=s.replace('global previous,last,earlier_identity','global previous,last,earlier_identity,kept_candidate')
s=s.replace('assert C.string_at(native,native_size.value)==data', '''assert C.string_at(native,native_size.value)==data
    bridge=C.c_void_p();bridge_size=C.c_size_t()
    assert d.nf_live_completed_wall_candidate(*earlier_identity,state_address,source_address,C.byref(bridge),C.byref(bridge_size))
    assert C.string_at(bridge,bridge_size.value)==data
    kept_candidate=(bridge,bridge_size.value,hashlib.sha256(data).hexdigest())
    counts['candidate_bridge_exact']+=1
    for wrong in [(earlier_identity[0],140,earlier_identity[2],earlier_identity[3]+1,state_address,source_address),(*earlier_identity,state_address+4,source_address),(*earlier_identity,state_address,source_address+1)]:
     rejected=C.c_void_p(123);rejected_size=C.c_size_t(456)
     assert not d.nf_live_completed_wall_candidate(*wrong,C.byref(rejected),C.byref(rejected_size)) and rejected.value==123 and rejected_size.value==456
     counts['candidate_atomic_rejections']+=1''')
s=s.replace("assert not errors,errors\n assert d.nf_state",'''assert not errors,errors
 rejected=C.c_void_p(123);rejected_size=C.c_size_t(456)
 assert not d.nf_live_completed_wall_candidate(*earlier_identity,50331840,139937176,C.byref(rejected),C.byref(rejected_size)) and rejected.value==123 and rejected_size.value==456
 counts['candidate_eviction_atomic']+=1
 assert kept_candidate and hashlib.sha256(C.string_at(kept_candidate[0],kept_candidate[1])).hexdigest()==kept_candidate[2]
 assert d.nf_state''')
s=s.replace("counts['reset_atomic']+=1",'''counts['reset_atomic']+=1
 assert not d.nf_live_completed_wall_candidate(*earlier_identity,50331840,139937176,C.byref(rejected),C.byref(rejected_size)) and rejected.value==123 and rejected_size.value==456
 assert hashlib.sha256(C.string_at(kept_candidate[0],kept_candidate[1])).hexdigest()==kept_candidate[2]
 d.nf_surface_free(kept_candidate[0]);kept_candidate=None
 counts['candidate_reset_copy_survival']+=1''')
p.write_text(s)
