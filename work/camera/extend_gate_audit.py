from pathlib import Path
p=Path('work/camera/test_texture_provenance.py');s=p.read_text().replace('enumeration=[]','enumeration=[];candidate_gates=[]',1)
s=s.replace('d.nf_extract_wall_candidate.argtypes=', '''d.nf_live_visibility_evaluate.argtypes=[C.c_uint64,C.c_uint32,C.c_uint32,C.c_uint32,C.c_void_p]
d.nfs_visibility_region_reconstruct.argtypes=[C.c_void_p,C.c_void_p,Read,C.c_void_p,C.c_void_p,C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t]
d.nf_extract_wall_candidate.argtypes=''')
s=s.replace("assert any(i['source']==139937176 for i in accepted) # Expected result, not selection input.",'''assert any(i['source']==139937176 for i in accepted) # Expected result, not selection input.
   result=C.create_string_buffer(4676);assert d.nf_live_visibility_evaluate(*earlier_identity,result)
   evaluated=result.raw;queue_count=struct.unpack_from('<H',evaluated,238)[0];assert queue_count<=20
   reciprocal=read_owned(0x08627700,65536)+read_owned(0x08637700,65536)
   @Read
   def gate_reader(ctx,address,out,amount):return d.nf_live_completed_snapshot_read(*earlier_identity,address,out,amount)
   wanted={i['source'] for i in accepted}
   for qi in range(queue_count):
    record=evaluated[256+qi*16:256+(qi+1)*16];region=struct.unpack_from('<H',record)[0]
    desc=read_owned(struct.unpack_from('<I',evaluated,20)[0]+region*48,48);first,vertex_count=struct.unpack_from('<HH',desc)
    start=struct.unpack_from('<I',evaluated,16)[0]+first*68
    if not any(start+i*68 in wanted for i in range(vertex_count)):continue
    state_copy=C.create_string_buffer(evaluated[:256],256);edges=C.create_string_buffer(32*52);stream=C.create_string_buffer(64*24)
    status=d.nfs_visibility_region_reconstruct(state_copy,record,gate_reader,None,reciprocal,edges,len(edges),stream,len(stream))
    for vi in range(vertex_count):
     address=start+vi*68
     if address in wanted:candidate_gates.append(dict(source=address,region=region,queue_index=qi,viewport=list(struct.unpack_from('<4H',record,2)),reconstruct_status=status,edge_flags=struct.unpack_from('<H',edges.raw,vi*52+48)[0] if status==1 else None))''')
s=s.replace('enumeration=enumeration,scope=', 'enumeration=enumeration,candidate_gates=candidate_gates,scope=');p.write_text(s)
