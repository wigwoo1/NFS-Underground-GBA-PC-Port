from pathlib import Path
import ctypes as C,os,json,struct,zlib,hashlib
base=Path(r'C:\NFSUG-Workspace');folder=base/'NFSUG-pc-road-recipe-tests'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
receipt=json.loads((folder/'recipe-test-report.json').read_text());assert sha(folder/'capture-host.dll')==receipt['core_sha256'];assert sha(folder/'road-source-recipes.nrrz')==receipt['archive_sha256'];assert sha(folder/'source-reciprocals.bin')==receipt['reciprocal_table_sha256']
with os.add_dll_directory('C:/msys64/mingw64/bin'):dll=C.CDLL(str(folder/'capture-host.dll'))
# No core is created or ROM/state loaded in this process.
replay=dll.nf_pc_road_recipe_replay;replay.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_void_p];replay.restype=C.c_int
table=(folder/'source-reciprocals.bin').read_bytes();archive=(folder/'road-source-recipes.nrrz').read_bytes();assert archive[:8]==b'NRRZ\x01\0\0\0';at=8;records=runs=0;output=C.create_string_buffer(8192*68)
while at<len(archive):
 n=struct.unpack_from('<I',archive,at)[0];at+=4;packet=zlib.decompress(archive[at:at+n]);at+=n;expected=struct.unpack_from('<Q',packet,40)[0];written=C.c_uint();assert replay(packet,len(packet),table,len(table),output,len(output),C.byref(written)) and written.value==expected and output.raw[:expected*68]==packet[80:80+expected*68];records+=1;runs+=expected
assert at==len(archive) and records==receipt['records'] and runs==receipt['road_runs']
r=dict(result='PASS_ALL_OWNED_ROAD_RECIPES_WITHOUT_CORE',records=records,road_runs=runs,commands_byte_exact=True,core_created=False,rom_or_state_loaded=False,archive_sha256=sha(folder/'road-source-recipes.nrrz'),core_dll_sha256=sha(folder/'capture-host.dll'),capture_report_sha256=sha(folder/'recipe-test-report.json'),test_source_sha256=sha(Path(__file__)),full_scene_60fps=False)
(folder/'archive-replay-report.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
