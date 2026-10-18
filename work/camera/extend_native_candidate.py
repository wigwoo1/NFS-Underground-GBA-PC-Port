from pathlib import Path
p=Path('work/camera/test_texture_provenance.py');s=p.read_text().replace('earlier_identity=None','earlier_identity=None;scene_palette_bytes={}')
s=s.replace('d.nf_wall_owner.argtypes=', 'd.nf_extract_wall_candidate.argtypes=[Read,C.c_void_p,C.c_uint32,C.c_uint32,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p]\nd.nf_wall_owner.argtypes=')
s=s.replace('assert agreed.raw==palette_bytes[0]', 'assert agreed.raw==palette_bytes[0]\n   scene_palette_bytes[h[4]]=b"".join(palette_bytes)')
s=s.replace("(root/'camera/candidate-owned-140-surface.bin').write_bytes(data)", '''@Read
    def plain_reader(ctx,address,out,amount):return d.nf_live_completed_snapshot_read(*earlier_identity,address,out,amount)
    native=C.c_void_p();native_size=C.c_size_t();bank=scene_palette_bytes[140]
    assert d.nf_extract_wall_candidate(plain_reader,None,state_address,source_address,bank,len(bank)//512,C.byref(native),C.byref(native_size))
    assert C.string_at(native,native_size.value)==data
    d.nf_surface_free(native)
    for address,palettes_to_test,palette_count in [(source_address,bank,0),(source_address+1,bank,len(bank)//512)]:
     rejected=C.c_void_p(123);rejected_size=C.c_size_t(456)
     assert not d.nf_extract_wall_candidate(plain_reader,None,state_address,address,palettes_to_test,palette_count,C.byref(rejected),C.byref(rejected_size)) and rejected.value==123 and rejected_size.value==456
    (root/'camera/candidate-owned-140-surface.bin').write_bytes(data)''')
p.write_text(s)
