from pathlib import Path
p=Path('work/camera/test_texture_provenance.py');s=p.read_text().replace('kept_candidate=None\n','kept_candidate=None;enumeration=[]\n',1)
s=s.replace("counts['candidate_before_future_scene']+=1",'''counts['candidate_before_future_scene']+=1
   # Discover only wall sources belonging to already captured road regions.
   ids=[struct.unpack_from('<5I',sections[5],8+i*20) for i in range(n)]
   existing={item[2] for item in ids if item[0]==2};seen=set();accepted=[];rejected=[]
   for road in ids:
    if road[0]!=1:continue
    owned_state=read_owned(road[1],256);desc=read_owned(road[2],48);first,vertex_count=struct.unpack_from('<HH',desc)
    assert 0<vertex_count<=32
    vertex_base=struct.unpack_from('<I',owned_state,16)[0]+first*68
    for vi in range(vertex_count):
     source_address=vertex_base+vi*68
     if source_address in seen or source_address in existing:continue
     seen.add(source_address);candidate=C.c_void_p();candidate_size=C.c_size_t()
     if d.nf_live_completed_wall_candidate(*earlier_identity,road[1],source_address,C.byref(candidate),C.byref(candidate_size)):
      record=C.string_at(candidate,candidate_size.value);d.nf_surface_free(candidate)
      accepted.append(dict(source=source_address,region=road[2],bytes=len(record),sha256=hashlib.sha256(record).hexdigest()))
      (root/'camera'/f'enumerated-140-{source_address}.bin').write_bytes(record)
     else:rejected.append(source_address)
   enumeration.append(dict(serial=140,road_regions=sum(i[0]==1 for i in ids),attempts=len(seen),accepted=accepted,rejected=rejected))
   assert any(i['source']==139937176 for i in accepted) # Expected result, not selection input.''')
s=s.replace('candidate_extractions=candidate_extractions,scope=', 'candidate_extractions=candidate_extractions,enumeration=enumeration,scope=');p.write_text(s)
