from pathlib import Path
p=Path('work/camera/test_texture_provenance.py');s=p.read_text().replace('if h[4]==140:earlier_identity=(epoch,h[4],h[5],h[6])','''if h[4]==140:
   earlier_identity=(epoch,h[4],h[5],h[6])
   early=C.c_void_p();early_size=C.c_size_t()
   assert d.nf_live_completed_wall_candidate(*earlier_identity,50331840,139937176,C.byref(early),C.byref(early_size))
   (root/'camera/candidate-at-publication-140.bin').write_bytes(C.string_at(early,early_size.value));d.nf_surface_free(early)
   counts['candidate_before_future_scene']+=1''');p.write_text(s)
p=Path('work/camera/make_single_candidate.py');s=p.read_text();start=s.index('a,s=read(140);');end=s.index('s[2]+=found[0]');s=s[:start]+'''a,s=read(140);ident=(2,50331840,139937176,37,0);n=struct.unpack_from('<I',s[2],4)[0]
assert ident not in [struct.unpack_from('<5I',s[5],8+i*20) for i in range(n)]
surface=(p/'candidate-at-publication-140.bin').read_bytes()
count,w,h=struct.unpack_from('<3I',surface);assert len(surface)==12+count*40+w*h*4
found=(surface,bytes(4)) # Checked bridge supports only unlit candidates.
'''+s[end:];s=s.replace('Single identity, future-sourced static candidate experiment','Single identity, earlier-owned static candidate experiment').replace('source_serial=141','source_serial=140').replace('Future material/state is intentionally borrowed only for this bounded diagnostic; requires earlier owned provenance before generalization.','Candidate extracted inside scene140 publication callback before scene141 exists. Supplied research identity; no automatic candidate selection.');p.write_text(s)
