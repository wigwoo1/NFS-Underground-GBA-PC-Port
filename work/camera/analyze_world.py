from pathlib import Path
import ctypes as C, collections, json, struct
root=Path('work/camera')
def records(path):
    data=path.read_bytes();position=0
    while position<len(data):
        header=struct.unpack_from('<21I',data,position);position+=84
        assert header[0]==0x3157464e
        blocks={}
        for i in range(header[4]):
            tag,address,size=struct.unpack_from('<3I',data,position);position+=12
            assert position+size<=len(data)
            blocks[tag]=(address,data[position:position+size]);position+=size
        yield {'pc':header[1],'frame':header[2],'id':header[3],'regs':header[5:],'blocks':blocks}
def u16(data,offset=0):return struct.unpack_from('<H',data,offset)[0]
events=[e for e in records(root/'world.bin') if e['pc'] in (0x03000304,0x03000d48,0x03001800,0x03002964,0x030032f0)]
counts=collections.Counter(hex(e['pc']) for e in events)
print('Events',counts)
native=C.CDLL(str((root/'native_camera.dll').resolve()))
native.nfs_camera_transform.argtypes=[C.c_void_p]*4+[C.c_uint]
pending=None;tested=0;face_sources=collections.defaultdict(set);camera_frames=collections.defaultdict(set)
draw_faces=set();materials=collections.defaultdict(set);camera_by_pointer=collections.defaultdict(set)
walls=collections.defaultdict(set);wall_count=0;linked_wall_count=0;world_points=set()
active={};wall_active_checked=0;wall_active_mismatches=[]
for e in events:
    if e['pc']==0x03001800:
        base=e['blocks'][5][0]
        world_points.update(base+i*68 for i in range(u16(e['blocks'][4][1],2)))
for e in events:
    b=e['blocks'];descriptor=b[4][0];source=b[5][0]
    if e['pc']==0x03000304:
        wall_count+=1;linked_wall_count+=source in world_points
        walls[source].add(struct.unpack_from('<I',b[8][1],40)[0])
        camera_frames[e['frame']].add(b[2][1].hex())
        camera_by_pointer[b[2][0]].add(b[2][1].hex())
        if b[1][0] in active:
            previous=active[b[1][0]]
            edge_offset=b[6][0]-previous['blocks'][6][0]
            expected_source=previous['blocks'][5][0]+(edge_offset//52)*68
            wall_active_checked+=1
            if edge_offset<0 or edge_offset%52 or expected_source!=source:
                wall_active_mismatches.append(e['id'])
        continue
    face_sources[descriptor].add(source)
    camera_frames[e['frame']].add(b[2][1].hex())
    camera_by_pointer[b[2][0]].add(b[2][1].hex())
    if e['pc']==0x03000d48:pending=e
    if e['pc']==0x03001800 and pending:
        p=pending['blocks']
        assert p[4][0]==descriptor
        count=u16(p[4][1],2)
        indices=[u16(p[5][1],i*68+42) for i in range(count)]
        offsets=bytearray((max([i for i in indices if i!=65535],default=0)+1)*32)
        for i,index in enumerate(indices):
            if index!=65535:
                assert len(p[10+i][1])==32
                offsets[index*32:index*32+32]=p[10+i][1]
        dest=C.create_string_buffer(p[6][1]);cb=C.create_string_buffer(p[2][1]);sb=C.create_string_buffer(p[5][1]);ob=C.create_string_buffer(bytes(offsets))
        assert native.nfs_camera_transform(cb,sb,ob,dest,count)==1
        assert dest.raw[:count*52]==b[6][1],('live transform',e['id'])
        tested+=1;pending=None
    if e['pc']==0x03001800:active[b[1][0]]=e
    if e['pc']==0x030032f0:
        draw_faces.add(descriptor)
        material=b[8][1]
        if len(material)==48:materials[descriptor].add(struct.unpack_from('<I',material,40)[0])
assert tested>0 and wall_active_checked>0, 'No usable world capture'
assert not wall_active_mismatches, 'Wall edge/source relationship changed'
report={'event_counts':dict(counts),'world_faces':len(face_sources),'faces_reaching_road_rasterizer':len(draw_faces),
        'stable_source_pointer_for_each_face':all(len(x)==1 for x in face_sources.values()),
        'native_transform_matches_live_game_calls':tested,
        'camera_addresses':{hex(k):len(v) for k,v in camera_by_pointer.items()},
        'frames_with_multiple_camera_values':sum(len(v)>1 for v in camera_frames.values()),
        'faces_with_multiple_texture_addresses':sum(len(v)>1 for v in materials.values()),
        'wall_draw_calls':wall_count,'wall_calls_linked_to_world_source':linked_wall_count,
        'world_wall_edges':len(walls),'wall_edges_with_multiple_textures':sum(len(v)>1 for v in walls.values()),
        'wall_current_transform_links_checked':wall_active_checked,'wall_current_transform_link_mismatches':wall_active_mismatches,
        'scope':'180-refresh driving sample. World descriptor/source correspondence observed, not a complete scene renderer.'}
(root/'world-analysis.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':
    for e in events[:4]:
        b=e['blocks'];print(hex(e['pc']),hex(b[4][0]),u16(b[4][1],2),'camera',struct.unpack('<12i',b[2][1]),'projection',b[3][1].hex())
