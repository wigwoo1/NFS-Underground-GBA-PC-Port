from pathlib import Path
import json,hashlib
from normalize_source_triangle_packets_candidate import normalize
p=Path('work/camera/prototype-runs');payload=(p/'source-sky-packet-payload.bin').read_bytes();ops=normalize((p/'source-sky-packet-records.bin').read_bytes(),payload)['ops'];groups={};i=None
for op in ops:
 if op['op']=='begin_frame':i=op['identity'][2];groups[i]=[]
 if i is not None:groups[i].append(op)
report=json.loads((p/'source-sky-packet-component.json').read_text());checks=[]
for row in report['source_packet_checks']:
 i=row['frame'];uploads={hashlib.sha256(payload[o['payload_offset']:o['payload_offset']+o['payload_bytes']]).hexdigest() for o in groups[i] if o['op'] in ('allocate_texture','update_texture') and o['payload_bytes']==153600}
 assert set(row['sky_hashes'])<=uploads
 weight=row['sky_weights'][1]
 assert any(o['op']=='draw_triangles' and not o['program'] and o['source_primitive']==7 and 0xbe2 in o['state']['enabled'] and abs(o['vertices'][0][9]-weight)<1e-7 for o in groups[i])
 checks.append(dict(frame=i,owned_planes_match_uploaded_bytes=True,blend_weight_matches=True))
r=dict(result='PASS_SOURCE_SKY_PACKETS_VS_RENDERER',checks=checks,scope='Five source samples; original240x160planes and fractionalblendweight verified, not live60fps cadence.')
(p/'source-sky-packet-parity.json').write_text(json.dumps(r,indent=2));print(r)
