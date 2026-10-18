from pathlib import Path
import ctypes as C, hashlib, json, struct,argparse
parser=argparse.ArgumentParser();parser.add_argument('--state',default='driving.state');parser.add_argument('--frames',type=int,default=180);parser.add_argument('--keys',type=int,default=1);parser.add_argument('--prefix',default='world');group=parser.add_mutually_exclusive_group();group.add_argument('--native-roads',action='store_true');group.add_argument('--native-walls',action='store_true');group.add_argument('--native-models',action='store_true');group.add_argument('--native-scenes',action='store_true');args=parser.parse_args()
root=Path('work').resolve()
d=C.CDLL(str(root/'nfsprobe.dll'))
d.nf_init.argtypes=[C.c_char_p,C.c_char_p]
d.nf_state.argtypes=[C.c_char_p,C.c_int]
d.nf_world_trace.argtypes=[C.c_char_p]
d.nf_native_roads.argtypes=[C.c_char_p]
d.nf_native_walls.argtypes=[C.c_char_p]
d.nf_native_models.argtypes=[C.c_char_p]
d.nf_native_scenes.argtypes=[C.c_char_p]
d.nf_dump.argtypes=[C.c_char_p,C.c_uint,C.c_uint]
rom=b'G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba'
hashes=[];scene_stats=None
for enabled in (False,True):
    assert d.nf_init(rom,b'')
    assert d.nf_state(str(root/args.state).encode(),0)
    d.nf_scene_enable(1)
    if enabled: assert (d.nf_native_roads if args.native_roads else d.nf_native_walls if args.native_walls else d.nf_native_models if args.native_models else d.nf_native_scenes if args.native_scenes else d.nf_world_trace)(str(root/f'camera/{args.prefix}.bin').encode())
    for frame in range(args.frames):d.nf_frame(args.keys)
    result={}
    for name,address,size in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000),('vram',0x06000000,0x18000)]:
        path=root/f'camera/{args.prefix}-trace-{int(enabled)}-{name}.bin'
        d.nf_dump(str(path).encode(),address,size)
        result[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    hashes.append(result)
    if enabled and args.native_scenes:
        stats=(C.c_uint32*4)();d.nf_native_scene_stats(stats);scene_stats=list(stats)
    d.nf_close()
assert hashes[0]==hashes[1], 'Capture changed game memory'
report={'frames':args.frames,'state':args.state,'keys':args.keys,'capture_preserves_memory':True,'hashes':hashes[0]}
if scene_stats is not None:report['scene_stats']=dict(zip(['closed_scenes','published','rejected','write_failures'],scene_stats))
(root/f'camera/{args.prefix}-capture-tests.json').write_text(json.dumps(report,indent=2))
print(report)
