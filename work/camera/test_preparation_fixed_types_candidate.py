import ctypes as C,json,sys
from pathlib import Path
import test_request_release_process_4k_candidate as reference
from owned_endpoint_road_planner import EndpointRoadPlanner
from owned_prepared_world_segmented_candidate import PreparedWorldMotion
from owned_precomputed_decode_release_candidate import PrecomputedSourceWorldSamples
report=json.loads(Path(sys.argv[1]).read_text());folder=Path(report['live_preparation_profiles'][0]['capture'])
source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')",'folder=Path('+repr(str(folder))+')')
ns={};exec(compile(source,'fixed-type-fixture','exec'),ns);ns['prepared'].close();ns['history'].close()
frames,scenes,rom,table=[ns[k] for k in ('frames','scenes','rom','table')]
def sample():
 history=EndpointRoadPlanner(rom,table);roads,_=history.plan(scenes[0].graph);prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom);owner=PrecomputedSourceWorldSamples(prepared,(.1,.35,.9))
 try:return [reference.fingerprint(owner,a) for a in (.1,.35,.9)]
 finally:owner.close();history.close()
expected=sample()
import owned_preparation_fixed_types_install_candidate as candidate
for _ in range(8):assert sample()==expected
for data in (b'',b'a',b'a\0b',bytes(range(256))):
 a=candidate.private_string_buffer(data);b=C.create_string_buffer(data);assert bytes(a)==bytes(b)
 other=candidate.private_string_buffer(data);assert C.addressof(a)!=C.addressof(other) and type(a) is type(other)
for size in (0,1,212,4096):assert bytes(candidate.private_string_buffer(size))==bytes(C.create_string_buffer(size))
out=dict(result='PASS_PRIVATE_FIXED_TYPE_SAMPLE_AND_BUFFER_PARITY',sample_comparisons=24,buffer_cases=8,private_addresses=True,scope='Complete captured frame/array/mask/detail/camera component parity; not native4K or live GC benefit.')
Path('work/camera/prototype-runs/preparation-fixed-types-20261009.json').write_text(json.dumps(out,indent=2));print(out['result'])
