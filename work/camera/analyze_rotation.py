from pathlib import Path
import collections,json,struct
from analyze_world import records
from test_rotation import native
root=Path('work/camera');pending=None;latest={};caller=None;passed=0;linked=0
camera_sides=collections.Counter();callers=collections.Counter();examples=[]
pose_matches=0;pose_calls=0;pose_sources=set()
for e in records(root/'world.bin'):
    b=e['blocks']
    if e['pc']==0x08023448:
        pose_calls+=1;pose_sources.add(hex(b[81][0]))
        expected=struct.pack('<9I',*[v*4&0xffffffff for v in struct.unpack('<9I',b[81][1])])
        pose_matches+=expected==b[83][1][:36]
    if e['pc']==0x0806db14:pending=e
    elif e['pc']==0x0806dc5c:
        assert pending
        p=pending['blocks'];expected=native(p[71][1],p[72][1])
        assert expected==b[73][1],(e['id'],'live combined matrix')
        passed+=1;latest[b[73][0]]=(pending,expected)
        callers[hex(pending['regs'][14])]+=1
        pending=None
    elif e['pc']==0x03002628:caller=e
    elif e['pc']==0x030045e0 and b[53][0] in latest:
        before,matrix=latest[b[53][0]]
        assert matrix[:36]==b[53][1][:36],(e['id'],'model rotation changed after composition')
        linked+=1
        assert caller
        camera=caller['blocks'][63][1]
        for tag,label in [(71,'left'),(72,'right')]:
            if before['blocks'][tag][1][:36]==camera[:36]:camera_sides[label]+=1
        if len(examples)<2:
            examples.append({'left_address':hex(before['blocks'][71][0]),'right_address':hex(before['blocks'][72][0]),
                'left':struct.unpack('<12i',before['blocks'][71][1]),'right':struct.unpack('<12i',before['blocks'][72][1]),
                'object_address':hex(caller['blocks'][62][0])})
assert passed>0 and linked>0
assert camera_sides=={'right':linked}, 'Shared camera input mismatch'
report={'result':'PASS','live_combinations':passed,'model_rotations_linked_to_combinations':linked,
        'shared_camera_rotation_input_matches':dict(camera_sides),'caller_return_addresses':dict(callers),
        'pose_matrix_capture_calls':pose_calls,'pose_Q12_to_Q14_matches':pose_matches,'pose_matrix_addresses':sorted(pose_sources),
        'examples':examples,'scope':'Driving sample only. The first loaded scene can predate capture.'}
(root/'rotation-analysis.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
