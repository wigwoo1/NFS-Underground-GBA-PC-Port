from pathlib import Path
p=Path('work/camera/test_texture_provenance.py');s=p.read_text();s=s.replace("assert captured[5]&256",'''# Enumerate the bounded 512-entry region table from the earlier state.
    descriptors=struct.unpack_from('<I',st,20)[0];vertices_base=struct.unpack_from('<I',st,16)[0]
    table=earlier_read(descriptors,512*48);owners=[]
    for ri in range(512):
     first,count=struct.unpack_from('<HH',table,ri*48)
     start=vertices_base+first*68
     if 0<count<=32 and start<=captured[2]<start+count*68 and (captured[2]-start)%68==0:owners.append(descriptors+ri*48)
    assert len(owners)==1,owners
    descriptor_address=owners[0];flags=struct.unpack_from('<H',src,46)[0]
    assert descriptor_address==captured[1] and flags==captured[5]
    assert flags&256''')
s=s.replace('captured[0],captured[1],captured[2],scratch,resolved_address,captured[5]', 'captured[0],descriptor_address,captured[2],scratch,resolved_address,flags')
s=s.replace("descriptor=captured[1],bytes=size.value,exact=True,limitation='Descriptor address and draw flags discovered from later draw; source bytes/material/palette from earlier owned scene.'", "descriptor=descriptor_address,flags=flags,owner_count=len(owners),bytes=size.value,exact=True,limitation='Target source identity is still supplied by the research case; owning descriptor and flags recovered independently from earlier state. Bounded table scan requires unique valid owner.'")
p.write_text(s)
