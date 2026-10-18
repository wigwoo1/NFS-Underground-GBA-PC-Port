"""Validate twelve owned complete generated packets against capture-source timing."""
from pathlib import Path
import csv,ctypes as C,json,hashlib,os
p=Path('work/camera');d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()))
source_prefix=os.environ.get('NF_REPLAY_SOURCE_PREFIX','road-attribute-motion');packet_prefix=os.environ.get('NF_REPLAY_PACKET_PREFIX','visibility-transition');report_prefix=os.environ.get('NF_REPLAY_REPORT_PREFIX','visibility-transition')
class Section(C.Structure):_fields_=[('data',C.c_void_p),('size',C.c_size_t)]
class Packet(C.Structure):_fields_=[('serial',C.c_uint),('begin',C.c_uint),('end',C.c_uint),('page',C.c_uint),('sections',Section*5)]
class Metadata(C.Structure):_fields_=[('data',C.c_void_p),('size',C.c_size_t),('mode',C.c_uint)]
d.nf_scene_packet_view.argtypes=[C.c_void_p,C.c_size_t,C.POINTER(Packet)]
d.nf_scene_packet_bounds.argtypes=[C.POINTER(Packet),C.POINTER(C.c_double),C.POINTER(C.c_void_p)]
d.nf_scene_packet_model_count.argtypes=[C.POINTER(Packet)]
d.nf_scene_world_metadata_all.argtypes=[Section,C.POINTER(Metadata),C.c_uint,C.POINTER(C.c_uint)]
sources=list(csv.DictReader((p/(source_prefix+'-sources.csv')).open()));assert len(sources)==12
records=[]
for i,source in enumerate(sources):
 data=(p/f'{packet_prefix}-{i:03}.packet').read_bytes();owned=C.create_string_buffer(data);packet=Packet()
 assert d.nf_scene_packet_view(owned,len(data),C.byref(packet))
 alpha=C.c_double();bounds=C.c_void_p();assert d.nf_scene_packet_bounds(C.byref(packet),C.byref(alpha),C.byref(bounds))
 assert abs(alpha.value-float(source['alpha']))<1e-10
 metadata=(Metadata*128)();count=C.c_uint();assert d.nf_scene_world_metadata_all(packet.sections[1],metadata,128,C.byref(count))
 models=d.nf_scene_packet_model_count(C.byref(packet));assert models
 modes=[metadata[j].mode for j in range(count.value)]
 records.append(dict(index=i,target=float(source['target']),source_pair=[int(source['older']),int(source['newer'])],alpha=alpha.value,bytes=len(data),models=models,world_surfaces=count.value,road_surfaces=sum(m in (5,6) for m in modes),wall_surfaces=sum(m in (2,3) for m in modes),section_sizes=[s.size for s in packet.sections],sha256=hashlib.sha256(data).hexdigest()))
assert sum(r['bytes'] for r in records)<=64*1024*1024
report=dict(result='PASS',packets=len(records),owned_packet_bytes=sum(r['bytes'] for r in records),distinct_source_pairs=len({tuple(r['source_pair']) for r in records}),records=records,scope='Complete packet parser validates every captured model/world/order/lighting section; bounds alpha matches source-camera manifest. Twelve adjacent displays cover limited transitions, not full route, original raster parity, smooth60fps or playable native logic.')
(p/(report_prefix+'-packet-tests.json')).write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='records'},indent=2))
