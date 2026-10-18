"""Decode actual original wall spans and compare source addresses to native C and game VRAM."""
import ctypes as C,hashlib,json,os,struct
from pathlib import Path
base=Path('C:/NFSUG-Workspace');folder=base/'NFSUG-wall-span-trace-fixtures';gpu=base/'NFSUG-android-local/app-restored-composition-gpu-tests';root=Path('Y:/CODEX/NFSUG-Native-PC-Port');rom=(root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();assert hashlib.sha256(rom).hexdigest()=='53817aec76a623dc2c7782ddf841f89f369aebe5a92a28c9afc69feaf914a593'
raw=(folder/'original-wall-spans.nws').read_bytes();events=[];at=0
while at<len(raw):
 h=struct.unpack_from('<45I',raw,at);assert h[0]==0x3153574e and h[1]==1 and h[2]==180+h[11] and at+h[2]<=len(raw);assert h[8]==0x030053e8,'Shaded original spans need explicit lookup decoding'
 events.append((h,list(h[28:45])));at+=h[2]
assert at==len(raw)
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(base/'NFSUG-android-wall-span-trace-local/capture-owned-text-host.dll'))
fn=d.nfs_wall_unshaded_addresses;U=C.c_uint32;fn.argtypes=[C.c_void_p,U,U,U,C.POINTER(U),C.POINTER(U)];fn.restype=C.c_int
writes=[];address_checks=0
for ordinal,(h,s) in enumerate(events):
 registers=h[12:28];count=registers[3];assert count<=320 and s[3]<=10 and 1<=s[4]<=1024
 source=(U*320)();destination=(U*320)();state=C.create_string_buffer(struct.pack('<17I',*s));assert fn(state,registers[1],registers[2],count,source,destination)
 shift=s[3];uvshift=15;texture=s[9];step=s[11]
 if s[6] and step>0x1b000:assert shift>=2;shift-=2;uvshift=17;texture=(texture+s[7])&0xffffffff
 texture=((texture+((s[13]&s[16])>>uvshift))&0xffffffff)&~1;dest=(registers[1]+((s[2]*(s[1]>>14))<<1))&0xffffffff;vertical=registers[2];mask=((s[4]<<15)-1)&0xffffffff
 for row in range(count):
  vertical&=mask;address=(texture+((vertical>>uvshift)<<shift))&0xffffffff;assert source[row]==address and destination[row]==dest;address_checks+=1
  offset=address-0x08000000;assert 0<=offset<len(rom);value=rom[offset]
  if value:
   for lane in range(2):
    physical=(dest&~1)+lane;page,cell=divmod(physical-0x06000000,0xa000)
    if page in (0,1) and cell<38400:writes.append((h[7],page,cell,value,ordinal,address,row,lane))
  dest=(dest+(s[2]<<1))&0xffffffff;vertical=(vertical+step)&0xffffffff
reference=json.loads((gpu/'original-hardware-wall-audit.json').read_text());state={};cursor=0;points=[]
# Source trace is chronological; query at each exact completed owner endpoint.
for point in sorted(reference['source_points'],key=lambda p:p['owner_end']):
 while cursor<len(writes) and writes[cursor][0]<=point['owner_end']:
  row=writes[cursor];state[(row[1],row[2])]=row;cursor+=1
 # Current fixture owner page comes from captured original scene metadata.
 capture=json.loads((folder/'source-fixture-capture-report.json').read_text());owner=next(r['owner'] for r in capture['road_records'] if r['owner']['serial']==point['owner_serial']);event=state.get((owner['page'],point['y']*240+point['x']));assert event,point
 item=dict(point);item.update(original_span_refresh=event[0],original_span_index=event[4],original_texture_address=event[5],original_span_row=event[6],mode4_lane=event[7],actual_span_index_value=event[3],matches_hardware=event[3]==point['original_hardware_index']);points.append(item)
assert all(p['matches_hardware'] for p in points)
summary={}
for p in points:
 key=(p['owner_serial'],p['original_last_writer_refresh'],p['original_span_refresh']);summary[key]=summary.get(key,0)+1
report=dict(result='PASS_ACTUAL_ORIGINAL_WALL_SOURCE_ADDRESSES',original_spans=len(events),span_trace_sha256=hashlib.sha256(raw).hexdigest(),source_destination_checks=address_checks,nonzero_lane_writes=len(writes),hardware_checks=len(points),all_actual_span_values_match_hardware=True,native_replay_mismatches=reference['mismatched'],groups=[dict(owner=k[0],reconstructed_writer=k[1],actual_original_span_writer=k[2],checks=v) for k,v in summary.items()],points=points,gpu_modified=False)
(folder/'original-wall-address-report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='points'},indent=2))
