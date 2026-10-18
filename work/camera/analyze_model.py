from pathlib import Path
import collections,json,struct
from analyze_world import records
from test_model import native
root=Path('work/camera')
pending=None;passed=0;culls=0;models=collections.Counter();callers=collections.Counter();matrices=collections.defaultdict(set)
caller=None;object_links=collections.defaultdict(set);translation_differences=collections.Counter()
def signed(v):return (v&0x7fffffff)-(v&0x80000000)
for e in records(root/'world.bin'):
    if e['pc']==0x03002628:caller=e
    if e['pc']==0x030045e0:pending=e
    elif e['pc']==0x03004770:
        assert pending is not None
        b=pending['blocks'];after=e['blocks'];count=struct.unpack_from('<H',b[52][1],36)[0]
        assert b[51][0]==after[51][0]
        scale=struct.unpack_from('<I',b[51][1],64)[0]
        x,y=struct.unpack_from('<hh',b[56][1],8)
        ok,dest=native(b[53][1],b[54][1],count,scale,x,y,b[55][1])
        assert ok==e['regs'][0],(e['id'],'live return')
        assert dest==after[55][1],(e['id'],'live model output')
        passed+=1;culls+=not ok;models[hex(b[52][0])]+=1
        callers[hex(struct.unpack_from('<I',b[57][1],112)[0])]+=1
        matrices[hex(b[53][0])].add(b[53][1].hex())
        if caller:
            cb=caller['blocks'];assert cb[64][0]==b[51][0]
            object_links[hex(cb[62][0])].add(hex(b[53][0]))
            cam=struct.unpack('<12i',cb[63][1]);matrix=struct.unpack('<12i',b[53][1])
            wx,wy,wz=struct.unpack_from('<3i',cb[62][1],12)
            x=(wx>>8)+cam[9];z=(wz>>8)+cam[11]
            expected=(signed(x*cam[0]+z*cam[6])>>14,(wy>>8)+cam[10],signed(x*cam[2]+z*cam[8])>>14)
            translation_differences[str(tuple(matrix[9+i]-expected[i] for i in range(3)))]+=1
        pending=None
assert passed>0,'No model transform calls captured'
assert sum(translation_differences.values())==passed, 'Missing object/camera linkage'
assert set(translation_differences)=={'(0, 0, 0)'}, 'Model translation differs from shared camera position'
report={'result':'PASS','live_model_calls':passed,'culled_live_models':culls,'model_descriptors':dict(models),
        'caller_return_addresses':dict(callers),'matrix_addresses_and_distinct_values':{k:len(v) for k,v in matrices.items()},
        'object_to_matrix_slots':{k:sorted(v) for k,v in object_links.items()},
        'model_translation_minus_shared_camera_object_position':dict(translation_differences),
        'scope':'Model transform/projection and shared-camera object translation match live output. Model orientation composition and complete vehicle coverage still need recovery.'}
(root/'model-analysis.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
